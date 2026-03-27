---
description: Full automation: Chargebee scan -> Sheet update -> Assignment -> Email drafts
---

## When to Run

Use for end-to-end processing of unpaid invoices. Trigger with `/payment-pipeline`.
**Prerequisite:** User MUST be logged into Chargebee and Google Sheets in the browser.

---

## Step 1: Scan Chargebee (Browser) 🕵️‍♂️

**Action:** Open `https://seomonitor-eur.chargebee.com/invoices` (with the unpaid filter).
**Goal:** Extract ALL unpaid invoices.
**Data needed:** Client Name, Amount, Date, Status, Invoice ID.

> "Scanning Chargebee for unpaid invoices..."

---

## Step 2: Read Tracker Sheet (Browser) 📊

**Action:** Open `https://docs.google.com/spreadsheets/d/14p5wgLjs4zj9-3yZHLBUe99qJ_d6vd0OJ6O--0av4xQ/edit`.
**Goal:** Read the "Monthly unpaid" tab.
**Data needed:** Existing Client names/Invoice IDs (to avoid duplicates).

> "Reading Google Sheet to check for existing records..."

---

## Step 3: Identify & Assign (Logic) 🧠

**Action:** Compare the two lists.
1.  **Filter:** Keep only invoices NOT already in the Sheet.
2.  **Assign:** Distribute new invoices 50/50 between **Sulejman** and **Katty**.
    *   Order by Date/Amount.
    *   1st New -> Sulejman
    *   2nd New -> Katty
    *   3rd New -> Sulejman
    *   ...

> "Found [N] new invoices. Assigning [X] to Sulejman and [Y] to Katty."

---

## Step 4: Update Tracker Sheet (Browser) 📝

**Action:** Append the new rows to the "Monthly unpaid" tab.
**Columns to Write:** Client, Date, Amount, Assigned Agent (Sulejman/Katty), Status (e.g. "Payment Due").

> "Writing new rows to Google Sheet..."

---

## Step 5: Draft Emails (Sulejman Only) 📧

**Action:** Filter the list for **Assignment = Sulejman**.
For each one, generate a draft using the logic from `/payment-chase`:
- **Friendly** (if technical/recent)
- **Firm** (if old)

**Output:**
Present the drafts in a batch for review.

> "Here are the drafts for YOUR assigned clients:"
