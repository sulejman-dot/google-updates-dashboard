# How does the Share of Clicks work with timeframes? 

> **Collection:** Customer Success
> **Last Modified:** 2025-07-10
> **Tags:** Ioana, share of clicks, share of clicks timeframe, timeframe

---

## ****

## **Why It Works This Way?**

The Share of Clicks metric is designed to show the current status (as of the end date) rather than a trend over time. 
The calculation uses the rankings data as of the end date selected in the timeframe, not an average over the entire period. This is why when you select a longer timeframe like "January 1 - March 31", you still get the same result as "March 1-31" - because both queries use March 31 as the reference date for the calculation.



## **What's the calculation?**

The share of clicks calculation in SEOmonitor works as follows:

1. When the `postShareOfVoice `method in  `SiteController.php `is called, it receives a request containing:
  - A start date and end date (in the intervals object)
  - Device type (desktop 'd' or mobile 'm')
  - Other filtering parameters like folder_id and keyword_ids

1. The controller then creates a `CompetitorsHandler `instance, passing along these parameters, and calls its `shareOfVoice()` method.
1. In the `shareOfVoice() `method, the handler calls `CompareStatsManager::fetchCompareShareOFvoice()` with the following key parameters:
  - The site hash and ID
  - **Only the end date** from the timeframe (not the start date)
  - The keyword IDs
  - Device type


Because **only the end date** is passed to the database query, not the start date, the expected behaviour is as follows:

  - When selecting March 1-31, you get the share of clicks as of March 31
  - When selecting April 1-28, you get the share of clicks as of April 28
  - When selecting January 1-March 31, you still get the share of clicks as of March 31


Looking at the SQL function `select_share_of_voice_v2`, it:

  - Calculates estimated visits based on keyword rankings and search volumes
  - Sums these values to get the total traffic for each competitor site
  - Calculates the percentage of traffic (share of clicks) for each competitor
  - But it doesn't take a date range - it's using the most recent data as of the end date



*For the Share of Click formula, check [this ](https://app.getguru.com/card/TkXKqG8c/How-is-the-Share-of-Clicks-calculated)Guru card.
