---
description: Generate payment chase drafts and update log (Smart Scheduling + Chargebee Retry)
---

## When to Run

Use to generate chase emails and track them. Trigger with `/payment-chase`.

---

## Step 1: Input Data

Ask:
> "Please provide:
> 1. **Client Name**
> 2. **Amount**
> 3. **Invoice Date**
> 4. **Failure Reason** (optional)"

---

## Step 2: Pre-Check (Chargebee Retry)

**Logic:**
If **Failure Reason** contains "funds" or "insufficient" or "authorize":
1.  Ask: > "Since the reason is '[Reason]', have you tried collecting the payment again in Chargebee today?"
2.  **If No:**
    > "⚠️ **Recommendation:** Try collecting in Chargebee first. Often these are temporary limits."
    > "Do you want to stop and try that, or proceed with drafting?"
    - **Stop:** End workflow.
    - **Proceed:** Continue to Step 3.

---

## Step 3: Select Template

Refer to `.agent/templates/payment-templates.md`.

**Logic:**
- **Technical Reason** → Template 1 (Friendly Nudge)
- **Old Date (>14 days)** → Template 3 (Firm Reminder)
- **Responsive but late** → Template 4 (Broken Promise) or Template 5 (Stalled)
- **Standard** → Template 2 (Professional)

---

## Step 4: Output Draft

Generate the draft using the selected template and input data.

---

## Step 5: Update Log

**CRITICAL STEP:**
Ask the user to confirm, then update `Collected Context/Payment-Chase-Log.md`:

1.  Find the client row (or add new).
2.  Update **Last Chase** to Today.
3.  Update **Status** (e.g., "Template [X] Sent").
4.  **Calculate Next Follow-up (Smart Scheduling):**
    - If **Template 1 or 5** (Friendly/Stalled) used: **Today + 3 days**
    - If **Template 2** (Professional) used: **Today + 2 days**
    - If **Template 3 or 4** (Firm/Broken) used: **Today + 1 day**

> "Log updated. Next follow-up auto-set for [Date] based on urgency."
