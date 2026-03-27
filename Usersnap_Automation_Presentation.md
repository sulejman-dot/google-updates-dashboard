# Usersnap Automation – Progress Overview

---

## Agenda
- Project background & objectives
- Key components & scripts
- What we have built so far
- Demo highlights
- Challenges & lessons learned
- Next steps & roadmap

---

## Project Background
- **Goal**: Keep Usersnap feedback items in sync with Intercom conversations.
- **Why**: Reduce manual copy‑paste, ensure accurate assignee, priority, status, and notes.
- **Stakeholders**: Support team, product managers, engineering.

---

## Core Objectives
1. **Automated data extraction** from Intercom (conversation ID, tags, priority, assignee).
2. **Update Usersnap items** with:
   - Assignee mapping
   - Priority sync
   - Status update
   - ClickUp URL notes
   - Labels from Intercom tags
3. **Robustness** – handle login expiration, continue on individual failures, deduplicate.

---

## Implemented Scripts
| Script | Purpose | Key Features |
|--------|---------|--------------|
| `usersnap_browser_sync.py` | Main automation driver | Playwright UI interaction, direct navigation to Usersnap items, resilient selectors, dry‑run mode |
| `usersnap_check_missing.py` | Detect Usersnap items lacking Intercom data | Scans project view, flags missing fields |
| `verify_item.py` | Verify a single Usersnap item update | Prints before/after state for debugging |
| `debug_usersnap_dom.py` | Helper for selector debugging | Dumps DOM snippets, visual inspection |
| `optimize_mac.sh` | (Utility) Improves local environment performance for script runs |

---

## What We Have Built So Far
- **Intercom discovery**: Pull conversation details via Intercom API, map tags to Usersnap labels.
- **Playwright automation**:
  - Log‑in flow with optional manual pause for MFA.
  - Direct URL navigation to a Usersnap item (bypassing search).
  - Stable selectors for assignee, priority, status fields.
  - ClickUp URL insertion into the Notes field, filtered to only ClickUp links.
- **Error handling**:
  - Continue processing after a single item failure.
  - Retry login on session expiry.
  - Deduplication logic to avoid updating the same item twice.
- **Dry‑run mode** (`--dry-run`) for safe testing without committing changes.
- **Logging**: Detailed console output and a CSV summary of processed items.

---

## Demo Highlights (Screenshots)
> *Before automation – empty fields*

![](real_usersnap_before.png)

> *After automation – populated fields*

    ![](real_usersnap_after_name.png)

---

## Challenges & Lessons Learned
- **Selector fragility** – Usersnap UI changes frequently; mitigated with fallback strategies and data‑attribute selectors.
- **Login session** – MFA sometimes interrupts automation; added a pause with a prompt to complete manual verification.
- **Rate limits** – Intercom API throttling required exponential back‑off.
- **Data consistency** – Ensured mapping tables (Intercom → Usersnap) are version‑controlled.

---

## Next Steps
1. **Full label sync** – map all Intercom tags to Usersnap labels.
2. **Priority mapping refinement** – support custom priority rules per team.
3. **CI/CD integration** – run the script nightly via GitHub Actions.
4. **Metrics dashboard** – track number of items synced, failures, and latency.
5. **User feedback loop** – add a quick “review” step for the support team before committing changes.

---

## Thank You!
*Questions?*
