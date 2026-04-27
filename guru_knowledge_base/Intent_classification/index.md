# Intent classification 

> **Collection:** Customer Success
> **Last Modified:** 2026-02-25
> **Tags:** intent

---

The logic behind intent classification is based on how competing pages rank in the SERP for that keyword.

We classify each landing page in the top results as informational, commercial, or transactional). Then we convert to percentages and apply this rule:



1. **Informational** wins only if it’s MORE than commercial + transactional combined
1. Otherwise, if **commercial > transactional** → commercial
1. Otherwise → **transactional**



**Why the stricter bar for informational?** Most SERPs naturally include some informational results (Wikipedia, blog posts, how-to guides). Without this threshold, a keyword with 40% informational + 35% commercial + 25% transactional would be wrongly labeled “informational” — even though 60% of the SERP serves a purchase-oriented intent.

The rule ensures “informational” only wins when it truly dominates the SERP, which makes the label more actionable for content strategy decisions.
