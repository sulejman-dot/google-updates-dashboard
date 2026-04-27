# Slack Bot → Oracle Cloud 24/7 Deployment Plan

> Created: 2026-04-24
> Goal: Eliminate ngrok dependency, run 24/7 on Oracle Cloud Always Free

---

## Decisions (locked)

| Choice | Decision |
|---|---|
| Host | Oracle Cloud Always Free, ARM Ampere A1 (4 OCPU / 24 GB RAM / Ubuntu 22.04) |
| Runtime | Docker + docker-compose (Flask + monitor + Caddy) |
| TLS | Caddy auto-HTTPS via Let's Encrypt |
| Hostname | DuckDNS subdomain (free) |
| Deploy | Private GitHub repo + `git pull && docker compose up -d --build` |
| Secrets | Plain files on VM, `chmod 600`, mounted into containers |
| Cutover | Parallel run 1 week, then switch Slack URLs |
| Comment monitor | Rewrite to ClickUp REST API (drop MCP), run in sidecar container with cron every 10 min |
| Out of scope | Guru KB extraction stays on Mac |

---

## Target architecture

```
                    Internet
                       │
                       ▼
         ┌─────────── VM (Oracle ARM) ───────────┐
         │                                       │
         │  Caddy :443  ─ auto-HTTPS ─►  Flask   │
         │                               :3000   │
         │                                       │
         │  Monitor sidecar  (cron every 10m)    │
         │    └─► calls ClickUp REST             │
         │    └─► posts to Slack via webhooks    │
         │                                       │
         │  Volumes: ./data (state), ./secrets   │
         └───────────────────────────────────────┘
```

The bot code itself (`slack_bot_server.py`) stays almost unchanged — the container is just a new deployment target.

---

## Phases

### Phase 1 — Code prep (on Mac)
1a. Audit `slack_bot_server.py`: confirm Slack signing-secret verification. If missing, add it (non-negotiable for public deployment).
1b. Extract hardcoded paths / hostnames. Move to env vars.
1c. Write `Dockerfile` for Flask server.
1d. Rewrite `clickup_comment_monitor_mcp.py` → `clickup_comment_monitor_rest.py` using `requests` + ClickUp Personal API Token. Keep `comment_state.json` contract identical.
1e. Write `Dockerfile` for monitor sidecar (minimal Python + cron).
1f. Write `docker-compose.yml` wiring Flask + monitor + Caddy.
1g. Write `Caddyfile` using `{$DOMAIN}` env var.
1h. Create `.env.example`, add real `.env` to `.gitignore`.
1i. Local smoke test: `docker compose up` on the Mac, curl `http://localhost/health`.

### Phase 2 — Oracle VM provision
2a. Sign up for Oracle Cloud Always Free (if not already).
2b. Request ARM Ampere A1 — 4 OCPU / 24 GB / Ubuntu 22.04 (may need retries if "out of capacity").
2c. SSH in. Harden: disable password auth, enable `ufw` (allow 22, 80, 443), install `fail2ban`.
2d. Install Docker + compose plugin.
2e. Open ports 80/443 in Oracle Cloud security list (separate from OS firewall).

### Phase 3 — DuckDNS + dynamic IP updater
3a. Create DuckDNS account, register subdomain `sulejman-slackbot.duckdns.org` (or similar).
3b. Point it at the VM's public IP.
3c. Install a systemd timer to update DuckDNS every 5 min (handles IP changes).

### Phase 4 — First deploy
4a. Push local repo to a new private GitHub repo (`slack-bot-cloud` or similar).
4b. SSH to VM, `git clone` the repo.
4c. `scp` `.env` and `service_account.json` to VM, `chmod 600`.
4d. `docker compose up -d --build`.
4e. Watch Caddy logs — confirm Let's Encrypt cert issued.
4f. `curl https://sulejman-slackbot.duckdns.org/health` from laptop.

### Phase 5 — Parallel validation
5a. Create a secondary Slack app pointed at the cloud URL (prod ngrok bot untouched).
5b. Add the test app to a private `#bot-test` channel.
5c. Exercise each of the 30+ endpoints; compare output to ngrok bot.
5d. Fix discrepancies (usually env vars, file paths, or timezone).
5e. Let comment monitor run for 48 hours; verify no duplicate notifications.

### Phase 6 — Cutover
6a. Update production Slack app URLs: slash commands, interactivity, event subscriptions — all change from ngrok to DuckDNS.
6b. Monitor logs on VM for 24–48 hours.
6c. If trouble, revert Slack URLs to ngrok domain; cloud bot can run in background.

### Phase 7 — Cleanup (week later)
7a. Stop Mac LaunchAgents if cloud bot is stable (`launchctl unload`).
7b. Archive `start_slack_bot.sh` and ngrok config under `cosmin folder/Sulejman Workspace/archive/`.
7c. Update `.claude/memory/sulejman.md` to reflect new architecture.
7d. Update `/start-slackbot` slash command (make cloud-aware, or remove).

---

## Repo layout (target)

```
slack-bot-cloud/
├── .gitignore                    # excludes .env, service_account.json, data/
├── .env.example                  # documented env vars
├── docker-compose.yml
├── Caddyfile
├── README.md
├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── slack_bot_server.py       # copied from current, signing-secret verified
│   └── ...helpers, templates...
├── monitor/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── clickup_comment_monitor_rest.py
│   ├── crontab
│   └── entrypoint.sh
└── data/                         # gitignored; comment_state.json lives here
```

---

## Env vars (first pass)

```
DOMAIN=sulejman-slackbot.duckdns.org
ACME_EMAIL=customer.success@seomonitor.com
SLACK_SIGNING_SECRET=...
SLACK_BOT_TOKEN=...
CLICKUP_API_TOKEN=...           # Personal API Token for REST monitor
GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/service_account.json
CHARGEBEE_API_KEY=...
SEOMONITOR_API_TOKEN=...
TZ=Europe/Bucharest
COMMENT_MONITOR_INTERVAL_MIN=10
```

Fill in from current `.env` when we get there.

---

## Risks / watch-outs

- **Oracle ARM capacity**: free tier "out of capacity" errors can persist for weeks. Fallback: AMD free tier (1 OCPU / 1 GB) — tighter but workable for a Flask bot.
- **Oracle reclaim**: idle free VMs can be reclaimed with notice. The comment monitor's every-10-min cron keeps the VM non-idle; also login to Oracle console roughly monthly.
- **Dynamic public IP**: Oracle compute gets a public IP by default but it can change on stop/start. DuckDNS updater covers this.
- **Slack rate limits**: ClickUp comment monitor fires at 10-min intervals — fine. Don't let it spiral.
- **Secret rotation**: when we SCP `.env`, the old token lives on two machines briefly. After cutover, rotate ClickUp + Slack tokens.

---

## Rollback

At any point before Phase 7, rollback is:
1. Revert Slack app URLs to ngrok domain
2. Re-enable Mac LaunchAgents if disabled
3. Cloud bot can keep running (it just won't receive Slack traffic)
