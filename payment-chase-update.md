---
description: Follow up on unpaid invoices efficiently (Updated)
---

## When to Run

Use when you need to chase a client for an overdue invoice. Trigger with `/payment-chase`.

---

## Step 1: Gather Invoice Details (Chargebee)

**Action:** Go to Chargebee (or ask me to check if connected).
*Note: I cannot currently access Chargebee directly, so please provide:*

1. **Invoice Date & Amount**: "When was it generated? How much?"
2. **Failure Reason**: "Why did the transaction fail? (e.g., Insufficient funds, Expired card, Do not honor)"
3. **Last Interaction**: "Have they responded to any auto-dunning emails?"

---

## Step 2: Determine Scenario

Based on the Chargebee data and client history, choose a path:

### Path A: The "Oops" (Technical Failure)
*Use if: Card expired, generic decline, client usually pays on time.*
- **Tone:** Helpful, assuming innocence.
- **Key msg:** "Looks like a bank glitch. Can you update your card?"

### Path B: The "Ghost" (Non-Responsive)
*Use if: No reply to previous automated emails, invoice 14+ days overdue.*
- **Tone:** Firm, escalating.
- **Key msg:** "We haven't received payment or a reply. Service may be paused."

### Path C: The "Promise Breaker" (Responsive but Unpaid)
*Use if: Client said "I'll pay Friday" but didn't.*
- **Tone:** Disappointed but professional.
- **Key msg:** "You mentioned this would be sorted. What's the status?"

---

## Step 3: Draft the Message

**Drafting for [Selected Path]...**

*Draft will include:*
- Invoice Details (from Step 1)
- Clear Call to Action (Link to portal)
- Specific reference to failure reason (if Path A) or previous promise (if Path C)

---

## Step 4: Review & Refine

> "How does this draft look? Does it match the client's situation?"

---

## Step 5: Save Record

Log the chase in `Collected Context/People/[ClientName].md` including the failure reason for future reference.
