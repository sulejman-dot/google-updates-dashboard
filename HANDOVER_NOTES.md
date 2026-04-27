# Handover Notes — Antigravity → Cowork Migration

> Migration date: 2026-04-24
> Source export: `../../Collected Context/Antigravity Export/` (backup, do not modify)

---

## What Was Migrated (Done)

| Export file | Target | Status |
|-------------|--------|--------|
| `HANDOVER_FOR_CLAUDE.md` | Read, used to design migration | ✅ |
| `RULES.md` | Folded into `CLAUDE.md` | ✅ |
| `MEMORY.md` | Split into `../../Collected Context/Claude Memory/sulejman/` (6 files) | ✅ |
| `WORKFLOWS.md` | Workflow files already present in Drive at `.agent/workflows/` — `CLAUDE.md` points to them | ✅ |
| `WORKFLOW_INVENTORY.md` | Reference only | ✅ |
| `FOLDERS.md` | Drive mounted at full `My Drive` path, matching Antigravity's scope | ✅ |
| `MCP.md` | See below — Intercom portable, ClickUp replaced by REST API skill | 🟡 partial |
| `TOOLS_AND_PERMISSIONS.md` | See below — different permission model | 🟡 partial |
| `UNPORTABLE.md` | Items listed below under "Lost in Migration" | ✅ |
| `OPEN_QUESTIONS.md` | Items listed below under "Open Questions" | ✅ |

---

## 🔴 Lost in Migration

### 1. Antigravity implicit memory (protobuf)
- **Files:** `~/.gemini/antigravity/implicit/*.pb` (~4.7 MB, binary)
- **Why lost:** Antigravity-proprietary format, no decoder.
- **Mitigation:** `MEMORY.md` captured what could be reconstructed. Some behavioral nuance will surface only through use — correct it in `Claude Memory/sulejman/` when it comes up.

### 2. `// turbo` / `// turbo-all` auto-run
- **Why lost:** Cowork's permission model approves tool calls at use time; there's no equivalent of `--dangerously-skip-permissions`. Read-only commands still require approval the first time.
- **Mitigation:** Workflow files keep the `// turbo` annotations as hints. As you use Cowork, mark commands you approve frequently for the approval UI to learn.

### 3. Antigravity browser session recordings
- Low impact — these were debug artifacts. Not replaced.

### 4. Antigravity conversation history / brain artifacts
- Implementation plans and walkthroughs from `~/.gemini/antigravity/brain/` don't transfer. Key decisions were captured in `MEMORY.md`.

---

## 🟡 Requires Action From You

### 1. ⚠️ Generate ClickUp API token
- **Why:** ClickUp MCP isn't in the Cowork connector registry. Claude will use the REST API via `.agent/skills/clickup-api.md` instead.
- **Action:**
  1. ClickUp → avatar → Settings → Apps → copy/generate API Token
  2. In a terminal: `export CLICKUP_API_KEY=xxx`
  3. Persist across shells: add the same line to `~/.zshrc` (or `~/.bashrc`)
- **Until this is done:** `/clickup-comments` routed through the API won't work. The LaunchAgent-based `clickup_comment_monitor_mcp.py` still needs to be rewritten to use the REST API (see #2).

### 2. ⚠️ Rewrite `clickup_comment_monitor_mcp.py` to use REST API
- Currently depends on ClickUp MCP. Swap the MCP calls for `curl`/`requests` calls per `.agent/skills/clickup-api.md`. Endpoints needed: `/team/2179830/task` (filter by assignee+status), `/task/{id}/comment`.

### 3. ⚠️ Connect Intercom MCP (OAuth, not the old bearer token)
- The Antigravity MCP config included a bearer token embedded in plain text. That token should be rotated.
- **Action:** Next time you need Intercom in Cowork, accept the "Connect" prompt — Cowork handles OAuth. Do not paste the old token anywhere.
- Old bearer token is still visible in `../../Collected Context/Antigravity Export/MCP.md` — consider rotating it in Intercom's admin console to be safe.

### 4. ⚠️ Resolve workflow canonicalisation
- Root `.agent/workflows/` has 5 files (team-shared, more polished).
- `.agent/workflows/` here has 11 files (personal, includes originals of the 5 overlapping files).
- Migration assumed the root versions are canonical for the 5 overlapping ones (`checkin-submit`, `checkout-submit`, `clickup-comments`, `journal`, `start-slackbot`). `CLAUDE.md` points there.
- **Confirm:** is that the right call? If not, update the table in `CLAUDE.md`.

### 5. ⚠️ Re-authenticate Guru extraction (if still running)
- Guru pipeline may use browser-scraped tokens. `guru_token_extractor.html` exists. Refresh frequency unknown — surface this the next time the Guru KB project is touched.

### 6. (Optional) Review archive candidates
- 6 workflows had no recorded use in the last 30 days: `/capture`, `/coach`, `/escalation-prep`, `/payment-chase`, `/payment-pipeline`, `/ticket-context`.
- They're still present in `.agent/workflows/` and wired up in `CLAUDE.md`. If you want to archive them, move the files to `.agent/workflows/archive/` and remove the rows from `CLAUDE.md`.

---

## ❓ Open Questions (Not Resolved in the Export)

These were in `Antigravity Export/OPEN_QUESTIONS.md` and remain open:

1. **`Collected Context/People/`** — referenced by `/daily-plan` and `/capture`, but the directory doesn't exist. Was it ever populated, or is this vestigial? If you want it, I can create stub profile files.
2. **`Collected Context/Projects/`** — same situation.
3. **`Collected Context/Notes/`** — same situation.
4. **`Shared Context/Product/`** — referenced by `/ticket-context` and `/escalation-prep`. Shared Context is a Drive shortcut I haven't explored yet. What lives there?
5. **Payment chase templates** — `/payment-chase` references `.agent/templates/payment-templates.md`, which was not found. Do you still have these?
6. **Daily checkin gap 2026-04-23** — submissions-backup.jsonl has a PM entry for that date but no `.md` file. Cosmetic.
7. **Cosmin's involvement** — the workspace is inside `cosmin folder/`. Does Cosmin work in this Drive? Will Claude's writes overlap with his?
8. **WBR data source** — `/wbr` Slack command serves it, `wbr_history.json` (27 KB) contains it — but where does it come from / how is it refreshed?
9. **SEOmonitor API access** — `seomonitor_api_tester.py` and `/test-api` exist. Should Claude have direct access? Is there a stable API key to load into the environment?

---

## Environment Differences (Cowork vs Antigravity)

A short reference so behaviors don't surprise you:

| Thing | Antigravity | Cowork |
|-------|-------------|--------|
| Slash commands | `/command` → `.agent/workflows/command.md` | `/command` → `CLAUDE.md` routes to the same workflow file |
| MCPs | Edit `~/.gemini/antigravity/mcp_config.json` | Connector registry with OAuth per server |
| Auto-run | `// turbo` in workflows | Per-tool approval at use time |
| Memory | Implicit protobuf + KI system | Markdown files in `Claude Memory/<namespace>/` |
| Browser recordings | WebP auto-capture | Not replicated |
| Rules / system prompt | None explicit | `CLAUDE.md` at project root |
| Per-person namespace | N/A | Folder per person under `Claude Memory/` |

---

## File Map After Migration

```
My Drive/
├── CLAUDE.md? ⚠️ (not created — Sulejman Workspace CLAUDE.md is the one in use)
├── .agent/workflows/           (team-shared, 5 files — canonical for overlaps)
├── Collected Context/
│   ├── Antigravity Export/     (backup, read-only, do not modify)
│   ├── Claude Memory/
│   │   └── sulejman/           (per-person memory namespace — 6 files)
│   ├── Daily Checkins/         (personal, by month)
│   └── submissions-backup.jsonl
├── Shared Context/             (symlink to team-shared folder)
│   └── AI Automation/Daily Checkins/
└── cosmin folder/
    └── Sulejman Workspace/
        ├── CLAUDE.md           (project instructions)
        ├── HANDOVER_NOTES.md   (this file)
        ├── .agent/
        │   ├── workflows/      (personal, 11 files)
        │   └── skills/
        │       └── clickup-api.md
        ├── slack_bot_server.py
        └── (the rest of your scripts)
```

---

## Next Steps Recommended Order

1. Generate ClickUp API token and export it.
2. Rewrite `clickup_comment_monitor_mcp.py` to use REST API (15-minute job).
3. Reconnect Intercom via Cowork's connector prompt next time you need it.
4. Answer the 9 open questions above when convenient — or let them surface naturally as Claude hits them.
5. If satisfied, consider rotating the old Intercom bearer token.
