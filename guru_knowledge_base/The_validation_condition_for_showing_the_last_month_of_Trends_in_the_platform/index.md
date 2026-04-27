# The validation condition for showing the last month of Trends in the platform

> **Collection:** Customer Success
> **Last Modified:** 2023-05-22
> **Tags:** Delia, Rank Tracker, search trends, seasonality, YOY, yoy trends

---

The new validation algorithm:

- As a validation threshold, we still count the keywords with full trends (>=11 months of SV trends and SV > 0)
- To validate the integrity of last month, we check that:
  - **EITHER**** **the number of keywords (with SV>0) is exactly the same as the threshold
  - **OR**** (**we have SVs for keywords counting more than 90% of the threshold, **AND** their average search volume (value) is over 80% of the search volume average over the past 3 years (this is dynamically provided to the DB query, and 3 years is the value for the top stats chart)**)**



For the SV month-by-month chart, we hide the previous month from the chart while the validation described above fails.


The validation rules are similar for the Top Stats YoY, but there's a difference in functionality - as it was already implemented, when the validation fails, we don't show the YoY.
