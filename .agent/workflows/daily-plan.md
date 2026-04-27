---
description: Team member day planning and briefing
---

## When to Run

Run this every morning before starting work. Trigger with `/daily-plan` or "plan my day".

---

## Step 0: Refresh ClickUp Comments Cache

Before anything else, refresh the ClickUp comments cache so the `/clickup-comments` Slack command has today's data. Run the `/refresh-clickup` workflow silently (no need to ask the user).

---

## Step 1: Confirm Today's Date

**ALWAYS start by stating the current date from the metadata timestamp.**

> "Today is **[Day], [Month] [Date], [Year]**."

---

## Step 2: Ask About Today

Ask:
> "What does your calendar look like today? Any key meetings or deadlines?"

This helps understand available time and commitments.

---

## Step 3: Review Context

Check:
1. `Collected Context/Daily Checkins/` — Yesterday's checkout (if exists)
2. `Collected Context/People/[Name].md` — Your profile with current priorities and projects
3. `Shared Context/` — Any company updates relevant to your role

If yesterday's checkout exists, ask:
> "I see from yesterday you had [unfinished items]. Do any of these carry over to today?"

---

## Step 4: Plan the Day

Help set a clear plan:

### Questions to Ask
- "What's the #1 thing that MUST get done today?"
- "What else is on your plate?"
- "Any blockers or things you're waiting on?"
- "How much focus time do you have between meetings?"

### Drive to Clear Outputs

Don't end until you have:

1. **Top 3 priorities** — In order of importance
2. **Time awareness** — How the day roughly breaks down
3. **Trade-offs acknowledged** — What's being delayed if needed

---

## Step 5: Output the Plan

Format as:

```markdown
## Today's Plan — [Date]

### 🎯 Top 3 Priorities
1. [Must do #1]
2. [Must do #2]
3. [Must do #3]

### ⏰ Today's Shape
- Meetings: [X hours]
- Focus time: [X hours]
- Key blocks: [What's scheduled when]

### ⚖️ Trade-offs
- [What might slip and that's okay]
```

---

## Step 6: Save

Save to `Collected Context/Daily Checkins/YYYY-MM/YYYY-MM-DD.md`

### New Step: Write Shared Copy
After writing my personal AM copy, also write a shared version:
- Create folder `/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Shared Context/AI Automation/Daily Checkins/YYYY-MM-DD/` if it doesn't exist
- Create file `Sulejman_YYYY-MM-DD.md` in that folder with the same AM content, formatted as:
  ```
  # YYYY-MM-DD — Sulejman
  ## 🌅 Morning Check-in
  [Same AM content as the personal copy]
  ```

### New Step: Update TODAY.md
- Read `/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Shared Context/AI Automation/Daily Checkins/TODAY.md`
- If the date is today: find my row and update it. If no row for me, add one.
- If the date is not today or file doesn't exist: create a fresh TODAY.md with today's date.
- Row format: `| Sulejman | ✅ HH:MM | ⏳ | AM: [2-3 sentence summary] |`

### New Step: Append to Weekly Digest
- Open `/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Shared Context/AI Automation/Daily Checkins/W{n}-digest.md` (create if it doesn't exist)
- Append: `**Sulejman — AM:** [1-2 sentence summary]`

### New Step: Append to JSONL
- Append one JSON line to `/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Shared Context/AI Automation/Daily Checkins/submissions.jsonl`
- Also append the same line to `Collected Context/submissions-backup.jsonl`
- Format: `{"ts":"...","date":"YYYY-MM-DD","week":"W{n}","user":"Sulejman","type":"AM","text":"[full AM text]"}`

Close with:
> "Your plan is saved. Good luck today! Run `/daily-review` at end of day to close out."
