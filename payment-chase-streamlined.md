---
description: Generate payment chase drafts from basic info
---

## When to Run

Use to quickly generate chase emails. Trigger with `/payment-chase`.

---

## Step 1: Input Data

Ask the user for the raw details in one go:

> "Please provide:
> 1. **Client Email**
> 2. **Amount**
> 3. **Invoice Date**
> 4. **Failure Reason** (if known, e.g. 'Cannot Authorize', 'Insufficient Funds')"

---

## Step 2: Generate Drafts

**DO NOT ask for tone/scenario.**
Instead, analyze the *Failure Reason* and *Date* to pick the best strategy, then **immediately generate the draft**.

**Logic:**
- **Technical Reason (e.g., Cannot Authorize)** → Use **Friendly/Technical Tone** (assume bank glitch).
- **No Reason / Old Date (>14 days)** → Use **Firm Tone**.
- **No Reason / Recent Date (<7 days)** → Use **Nudge Tone**.

---

## Step 3: Output

Present the draft clearly:

```text
Subject: ...
Body: ...
```

Then ask:
> "Shall I save this chase to their client record?"
