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

Close with:
> "Your plan is saved. Good luck today! Run `/daily-review` at end of day to close out."
