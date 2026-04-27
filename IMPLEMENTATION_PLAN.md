# Implementation Plan — Bring All 10 Projects Into Claude

> Created: 2026-04-24
> Prior docs: `DEPLOYMENT_PLAN.md` (Slack bot cloud migration, still valid)
> Canonical Claude config: `CLAUDE.md` at this directory; memory at `../../Collected Context/Claude Memory/sulejman/`

---

## Scope

Ten projects / automations / dashboards from the Antigravity era need to be fully integrated with Claude and working reliably:

1. Daily Check-in/Check-out System
2. Slack Bot (30+ endpoints, Flask)
3. ClickUp Comment Monitor (LaunchAgent)
4. Payment Chase Pipeline (Chargebee → Sheets → email drafts)
5. Usersnap → ClickUp Sync
6. SEO Intelligence Dashboard (5x/day cron)
7. ClickUp Dashboard (Netlify, refresh-on-demand)
8. Guru Knowledge Base (extraction + `#technical-questions` monitor)
9. WBR Dashboard (Weekly Business Review, Slack-bot endpoint)
10. Guru Dashboard (KB card browser)

For each: define "done", identify gaps, execute.

---

## Decisions (locked on 2026-04-24)

| Decision | Value |
|---|---|
| Canonical Claude config | `Sulejman Workspace/CLAUDE.md` + `Collected Context/Claude Memory/sulejman/` |
| Memory organization | 6 thematic files (profile, preferences, projects, collaborators, reference, README) — keep |
| My redundant `/My Drive/.claude/` copy | Delete (Wave 0) |
| Hosting strategy | Case-by-case — decide per project in its Wave |
| Guru card generator current state | Built but not running — Wave 2 will wire up scheduling |
| Usersnap + Payment Chase | Keep, revive properly in Wave 4 |

---

## Waves

### Wave 0 — Reconcile Claude configs ★ SHOULD GO FIRST

**Why first:** two parallel configs means slash commands might route to different files depending on which CLAUDE.md Claude loads. One source of truth.

**Tasks:**
- [x] Archive old `/My Drive/.claude/` + root CLAUDE.md into `/My Drive/.claude-cowork-archive-2026-04-24/` (done 2026-04-24; README inside marks it safe to delete)
- [x] Replace `/My Drive/CLAUDE.md` with a lean pointer that routes to the canonical config (done 2026-04-24 via `/init`; ~30 lines, no duplication) — kept instead of a plain delete so Claude sessions launched from `/My Drive` still find the canonical config
- [ ] Verify `Sulejman Workspace/CLAUDE.md` routes all 8 active slash commands to `.agent/workflows/*.md` with correct canonical choice (root vs nested for the 2 overlapping ones)
- [ ] Smoke test: open Claude Code in workspace, type `/daily-plan`, confirm it loads the right file

**Deliverable:** one canonical config at Sulejman Workspace level, plus a pointer stub at workspace root.

---

### Wave 1 — Slack Bot cloud migration ★ IN FLIGHT

Already covered by `DEPLOYMENT_PLAN.md`. Phase 1 complete. Phases 2–7 remaining:

- Phase 2 — Provision Oracle Ampere A1 VM (4 OCPU / 24 GB / Ubuntu 22.04)
- Phase 3 — DuckDNS subdomain + dynamic IP updater
- Phase 4 — First deploy via private GitHub repo + `docker compose up`
- Phase 5 — Parallel validation (secondary Slack app, 48h test)
- Phase 6 — Cutover Slack app URLs
- Phase 7 — Cleanup Mac LaunchAgents + ngrok

**Deliverable:** Slack bot + ClickUp comment monitor running 24/7 on Oracle, no Mac dependency.

Includes **Project #2 Slack Bot** and **Project #3 ClickUp Comment Monitor**.

---

### Wave 2 — Guru Knowledge Base integration

Covers **Project #8 Guru KB** and **Project #10 Guru Dashboard**.

**Current state:**
- `guru_extractor.py` — scrapes cards from Guru (browser-scraped token via `guru_token_extractor.html`)
- `guru_card_generator.py` — scans `#technical-questions` Slack channel, classifies threads, generates Q&A content, sends review notifications
- `guru_daily_scan.sh` — cron wrapper, **not currently running** (per user, Wave 2 wires it up)
- `guru-dashboard/` — static site for browsing cards (2.6 MB, currently not deployed)
- `guru_knowledge_base.md` — 8 MB MD file with 588 base64-encoded images
- `guru_cards_tracker.json` — tracks which threads have been processed

**Target state:**
1. `guru_card_generator.py` runs automatically (daily or twice-daily) on a schedule
2. Schedule lives where decided in Wave 2 kickoff (Mac cron vs Oracle sidecar)
3. Token refresh: a `/guru-token` slash command that walks through the token-extraction flow when the current token expires
4. Review workflow: `.agent/workflows/guru-review.md` slash command that reads `guru_cards/pending_review/` and walks through approvals
5. `guru-dashboard/` deployed to Netlify (or wherever — decide in Wave)
6. Memory updated: `projects.md` reflects current Guru architecture

**Tasks:**
- [ ] Decide hosting: Mac cron vs Oracle sidecar (cloud makes more sense if Wave 1 is already on Oracle)
- [ ] Wire up `guru_daily_scan.sh` with LaunchAgent plist (if Mac) or Docker cron (if Oracle)
- [ ] Write `/guru-review` slash command
- [ ] Document token-refresh procedure as `/guru-token`
- [ ] Deploy `guru-dashboard/` to Netlify (or confirm existing deployment)
- [ ] Update `.claude/memory/sulejman/projects.md` (or equivalent)

---

### Wave 3 — SEO Intelligence Dashboard

Covers **Project #6 SEO Intelligence Dashboard** and **Project #7 ClickUp Dashboard**.

**Current state:**
- `google_update_monitor.py` (53 KB) — monitors Google algorithm updates, competitor activity, MozCast volatility
- Cron on Mac refreshes data 5x/day
- Dashboard deployed to Netlify (`dashboard/` folder → git → Netlify)
- `wbr_history.json` ends up inside `dashboard/` too
- `/refresh-clickup` slash command already ported (ClickUp Dashboard side)

**Target state:**
1. Data refresh runs 24/7 (on Oracle or Mac — decide in Wave)
2. `/seo-update` slash command: "what's new with Google algorithms this week?" — queries `dashboard_data.json`, summarizes
3. `/volatility` slash command: summarizes MozCast SERP volatility
4. Dashboards stay on Netlify (no change)

**Tasks:**
- [ ] Decide hosting for the cron
- [ ] Port the cron schedule to Oracle if needed
- [ ] Write `/seo-update` and `/volatility` slash commands that read the JSON data
- [ ] Memory doc: note which endpoints/files serve what

---

### Wave 4 — Legacy integrations: Usersnap, Payment Chase, WBR

Covers **Projects #4 (Payment Chase), #5 (Usersnap), #9 (WBR)**.

**Current state:**
- **Usersnap sync**: 6 Python scripts, last active Jan-Feb 2026. Syncs Usersnap feedback items → ClickUp tasks.
- **Payment Chase**: workflows were archive candidates, templates lost. Chargebee API + Google Sheets + email drafts.
- **WBR**: 4 Python files (`wbr_enhanced.py`, `wbr_data_store.py`, `wbr_reader.py`, `wbr_history.json`). Served by Slack bot's `/wbr` endpoint.

**Target state:**
1. **Usersnap**: `/usersnap-sync` slash command that triggers a fresh sync. Cron optional.
2. **Payment Chase**: revived with new email templates (you'll draft). `/payment-chase` command that runs the full pipeline.
3. **WBR**: `/wbr-summary` Claude slash command that reads `wbr_history.json` and produces a narrative summary (distinct from the existing `/wbr` Slack bot endpoint).

**Tasks:**
- [ ] Audit Usersnap scripts — what still works? What's bitrotted?
- [ ] Draft new payment chase email templates
- [ ] Write 3 new slash commands: `/usersnap-sync`, `/payment-chase`, `/wbr-summary`
- [ ] Update memory

---

### Wave 5 — Cleanup + final documentation

**Tasks:**
- [ ] Remove Mac LaunchAgents superseded by Oracle deployments (per Wave 1+2 decisions)
- [ ] Archive old `.agent/workflows/*.md` files that are now unused (the original nested workflows if they weren't picked as canonical)
- [ ] Update `HANDOVER_NOTES.md` with final state
- [ ] Refresh `.claude/memory/sulejman/projects.md` to reflect new architecture
- [ ] Confirm daily rhythm still works end-to-end

---

## Estimated effort

| Wave | Rough time | Can do in | Notes |
|---|---|---|---|
| 0 Reconcile | 15 min | Any session | Quick cleanup |
| 1 Slack Bot cloud | 4–8 hours | Claude Code | Includes Oracle signup wait time |
| 2 Guru KB | 2–4 hours | Claude Code | Depends on hosting decision |
| 3 SEO Dashboard | 2 hours | Claude Code | Slash commands + memory |
| 4 Legacy trio | 3–5 hours | Claude Code | Most of this is drafting payment templates |
| 5 Cleanup | 1 hour | Either | Final polish |

Waves can be parallelized slightly (e.g., 3 + 4 simultaneously), but 0 must be first and 1 should finish before 2 so both have the same hosting answer.

---

## Where to pick this up next session

Best in **Claude Code** (`cd` into the workspace, `claude`). Paste this plan as the first thing. Say "start Wave 0" or "continue Phase 2 of DEPLOYMENT_PLAN.md".

Outstanding context from today's Cowork session that Claude Code won't have:
- Slack signing-secret middleware is already active on Mac (commit ready)
- `safe_respond` bug was fixed today
- `slack-bot-cloud/` repo scaffold is complete
- `.backup-pre-cloud-migration/` contains pre-patch copies of 4 files
- The 4 hardcoded-token files have been patched

All of that is on disk — Claude Code will see it when it reads the relevant files.
