---
description: End-of-day reflection and scoring
---

## When to Run

Run at the end of each workday. Trigger with `/daily-review` or "end of day".

---

## Step 1: Load Today's Plan

Read `Collected Context/Daily Checkins/YYYY-MM/YYYY-MM-DD.md` (today's date).

**If file exists:**
- Display the morning priorities
- Ask: "How did you do on these today?"

**If no file exists:**
- Ask: "What were your main priorities today? Let's review them."

---

## Step 2: Review Each Priority

For each priority:

> "[Priority] — Done, partially done, or not done? Quick note if helpful."

Track:
- ✅ Done
- 🔄 Partially done (what's left?)
- ❌ Not done (why?)

---

## Step 3: What Else Happened

Ask:
> "Anything else you worked on that wasn't planned?"

Captures:
- Urgent things that came up
- Valuable unplanned work

---

## Step 4: Score the Day

Ask for a quick self-score:

> "On a scale of 1-10, how would you rate today overall?"

Benchmarks:
- **8-10:** Great day, high execution
- **5-7:** Decent, some drift
- **1-4:** Off track

---

## Step 5: Quick Reflection + Tomorrow

Ask:
- "What worked well today?"
- "What would you do differently?"
- "What's your #1 priority for tomorrow?" (drive to specific answer, not vague)

---

## Step 6: Estimate Time Saved

Based on everything discussed today, provide an estimate:

> "Based on our work today — [summarize what you helped with: planning, prep docs, coaching, etc.] — I estimate I saved you approximately **[X] minutes/hours** compared to doing this manually."

Be specific about what you counted:
- Morning planning: ~15 min saved
- Client prep doc: ~30 min saved
- Research/context gathering: ~20 min saved
- Etc.

**Include the total in the checkout summary below.**

---

### New Step: Scan for Second Brain Journals
Before writing PM content, scan `/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Shared Context/AI Automation/Daily Checkins/YYYY-MM-DD/` for files matching `Sulejman_*.md` (excluding the check-in file `Sulejman_YYYY-MM-DD.md`). Extract use case categories and time saved from each journal found.

## Step 7: Save

Update `Collected Context/Daily Checkins/YYYY-MM/YYYY-MM-DD.md`:

```markdown
## Evening Checkout

### Priority Review
1. [Priority 1] — ✅/🔄/❌ [Notes]
2. [Priority 2] — ✅/🔄/❌ [Notes]
3. [Priority 3] — ✅/🔄/❌ [Notes]

### What Else
- [Unplanned work]

### Day Score: X/10

### AI Coach Time Saved: ~Xh Xmin
- [Breakdown of what saved time]

### Reflection
[One insight or learning]

### Tomorrow's #1 Priority
[What must get done tomorrow]
```

### New Step: Update Shared Copy (PM)
- Read the existing AM file at `/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Shared Context/AI Automation/Daily Checkins/YYYY-MM-DD/Sulejman_YYYY-MM-DD.md`
- Append the PM section at the bottom WITHOUT modifying the AM content
- The PM section MUST include: What Was Delivered, **Time Saved** (total hours + breakdown by task), AI Sessions table (if journals found), and Day Score
- If no AM file exists (morning was skipped), create the file with just the PM section

### New Step: Update TODAY.md (PM)
- Change my PM column from ⏳ to ✅ HH:MM
- Extend the Summary with PM highlights AND include **time saved** (e.g. "~4h saved via AI")

### New Step: Append PM to Weekly Digest
- Find today's date section and my AM entry
- Append below it: `**Sulejman — PM:** [1-2 sentence summary]`

### New Step: Append PM to JSONL
- Same as AM but with `"type":"PM"` and additional fields: `sessions_total`, `use_cases`, `planning_mode_pct`, `time_saved_hours`
- Example: `{"ts":"...","date":"YYYY-MM-DD","week":"W{n}","user":"Sulejman","type":"PM","text":"...","sessions_total":3,"use_cases":["automation","reporting"],"planning_mode_pct":67,"time_saved_hours":4}`

---

## Step 8: Generate Team Checkout Message

Create a short checkout message for Slack:

```markdown
**Checkout — [Name]**
✅ Done: [1-2 key completions]
🔄 In progress: [1 thing carrying over]
📊 Day score: X/10
⏱️ AI Coach saved: ~Xh
```

This goes to the Slack bot via `/daily-review`.

---

Close with:
> "Logged. Nice work today. See you tomorrow with `/daily-plan`."
