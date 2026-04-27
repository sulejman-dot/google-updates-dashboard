# Why do I see the same seasonality in Forecast scenarios done on different groups of keywords?

> **Collection:** Customer Success
> **Last Modified:** 2024-02-20
> **Tags:** Delia, forecast, Forecast configuration, organic traffic, scenario, seasonality

---

This happens when the scenarios are created on the same date as the top 10 keywords are taken into account, no matter what groups you select, because these keywords would impact the future organic traffic even if you don't include them in your forecast.


For non-pitching campaigns, the "Search Seasonality" percentage is computed as: [Month "Top10 Keywords SV" / First month's "Top10 Keywords SV"] * 100

Where "Top10 Keywords SV" is the sum of search volumes for the keywords with desktop ranks in top 10 when the Forecast is created.
