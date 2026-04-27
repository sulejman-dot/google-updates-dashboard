# Claude Project Instructions — Sulejman / SEOmonitor CS

> Migrated from Antigravity on 2026-04-24.
> Export backup lives at `../../Collected Context/Antigravity Export/` — do not modify or delete.

## Identity

Working with **Sulejman**, Customer Success engineer at SEOmonitor.
- Email: `sulejman@seomonitor.com`
- Timezone: Europe/Bucharest (UTC+2/+3)
- Style: fast, technical, builds his own tooling in Python/Flask

Other people: **Cosmin** (manager), **Katty** (CS colleague, splits payment chase 50/50), **Delia** (CS colleague).

## Communication Rules

1. Concise. Summary at end of turn. No verbose explanations.
2. `hi` = casual greeting. Don't launch into a summary or ask what he needs.
3. Use structured markdown with emoji section headers (🎯 ⏰ ⚖️ 🌅 🌙).
4. Don't explain Python, Flask, or git basics.
5. State the date at the start of `/daily-plan`.
6. If he types a slash command, start immediately — no "would you like me to".

## Slash Commands → Workflow Files

When Sulejman types one of these, open the matching `.md` and follow its steps verbatim.

| Command | File (relative to this CLAUDE.md) |
|---------|-----------------------------------|
| `/daily-plan` | `.agent/workflows/daily-plan.md` |
| `/daily-review` | `.agent/workflows/daily-review.md` |
| `/checkin-submit` | `../../.agent/workflows/checkin-submit.md` (root, canonical) |
| `/checkout-submit` | `../../.agent/workflows/checkout-submit.md` (root, canonical) |
| `/journal` | `../../.agent/workflows/journal.md` (root, canonical — richer) |
| `/start-slackbot` | `../../.agent/workflows/start-slackbot.md` (root, canonical) |
| `/clickup-comments` | `../../.agent/workflows/clickup-comments.md` (root, canonical) |
| `/refresh-clickup` | `.agent/workflows/refresh-clickup.md` |
| `/capture` | `.agent/workflows/capture.md` |
| `/coach` | `.agent/workflows/coach.md` |
| `/escalation-prep` | `.agent/workflows/escalation-prep.md` |
| `/payment-chase` | `.agent/workflows/payment-chase.md` |
| `/payment-pipeline` | `.agent/workflows/payment-pipeline.md` |
| `/ticket-context` | `.agent/workflows/ticket-context.md` |

Where files exist in both locations with different content, the root `.agent/workflows/` copy is treated as canonical per the migration decision. This is flagged in `HANDOVER_NOTES.md` as still open for Sulejman to confirm.

## Dual-Write Pattern (Non-Negotiable)

Every daily checkin/checkout writes to **all six** of these. If a step fails, tell Sulejman which one — do not silently skip.

1. Personal: `../../Collected Context/Daily Checkins/YYYY-MM/YYYY-MM-DD.md`
2. Shared: `../../Shared Context/AI Automation/Daily Checkins/YYYY-MM-DD/Sulejman_YYYY-MM-DD.md`
3. `../../Shared Context/AI Automation/Daily Checkins/TODAY.md` — update Sulejman's row
4. `../../Shared Context/AI Automation/Daily Checkins/W{n}-digest.md` — append entry
5. `../../Shared Context/AI Automation/Daily Checkins/submissions.jsonl` — one JSON line
6. `../../Collected Context/submissions-backup.jsonl` — same JSON line (backup)

JSONL line format (AM):
```json
{"ts":"YYYY-MM-DDTHH:MM:SS+TZ","date":"YYYY-MM-DD","week":"W{n}","user":"Sulejman","type":"AM","text":"[full AM text]"}
```

JSONL line format (PM):
```json
{"ts":"...","date":"YYYY-MM-DD","week":"W{n}","user":"Sulejman","type":"PM","text":"[full PM text]","sessions_total":N,"use_cases":["..."],"planning_mode_pct":N,"time_saved_hours":N.N}
```

## Privacy Guard

**Never log** any of these to the dual-write files or journals:
- Employee performance, HR, compensation, salary
- Confidential business strategy or board-level decisions
- Legal matters or contract details
- Customer PII (names, emails, account numbers)

If the work touches any of these, say:
> ⚠️ This session contains sensitive content that cannot be journaled. Skipping.

## Memory

Per-person memory at `../../Collected Context/Claude Memory/sulejman/`:
- `profile.md` — identity, role, working hours, energy patterns
- `preferences.md` — communication/workflow/technical preferences + what NOT to do
- `projects.md` — ongoing projects (Guru KB, Slack bot, dashboards, etc.)
- `collaborators.md` — Cosmin, Katty, Delia
- `reference.md` — key paths, URLs, time-saved baseline

Read these at the start of a new conversation before responding to anything non-trivial.

## Tool Access

### ClickUp — API (no MCP in Cowork)
Use `.agent/skills/clickup-api.md`. Auth via `$CLICKUP_API_KEY` env var. Workspace ID: `2179830`. Base URL: `https://api.clickup.com/api/v2`.
**Pending:** Sulejman needs to generate and export the token — see `HANDOVER_NOTES.md`.

### Intercom — Cowork MCP
Available via the Cowork connector registry. Re-authenticate (OAuth); **do not** reuse the Antigravity bearer token. The first time you need it in a session, call `suggest_connectors` so Sulejman can connect it.

### Slack bot
Local Flask server at `localhost:3000`, tunneled via `prevertebral-preadequately-lezlie.ngrok-free.dev`. Start with `/start-slackbot`. 30+ endpoints in `slack_bot_server.py`.

### File system
Full read/write inside `My Drive/`. Treat `Collected Context/Antigravity Export/` as read-only backup.

### Terminal
Each bash call requires user approval at use time. The Antigravity `// turbo` / `// turbo-all` annotations don't transfer to Cowork — if a workflow file contains them, treat as a hint that the command is safe to auto-run, but the Cowork approval step still fires. Document any commands that should be pre-approved in Cowork settings later.

## Key Paths (absolute)

- Workspace root: `/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive`
- Personal scripts: `.../My Drive/cosmin folder/Sulejman Workspace/`
- Personal checkins: `.../My Drive/Collected Context/Daily Checkins/`
- Shared checkins: `.../My Drive/Shared Context/AI Automation/Daily Checkins/`
- Slack bot: `.../cosmin folder/Sulejman Workspace/slack_bot_server.py`
- Knowledge base: `.../cosmin folder/Sulejman Workspace/guru_customer_success_knowledge_base.md`

## Metric to Keep Visible

Sulejman measures AI value in **hours saved per day**. Track explicitly in every PM checkout. Baseline: 2.0–3.5 h/day as of April 2026.
