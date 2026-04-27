# How SEOmonitor Detects Seasonal Keywords - Revised Explanation - internal documentation

> **Collection:** Customer Success
> **Last Modified:** 2025-03-19
> **Tags:** Delia, M test, rank tracker v2, seasonal, seasonal keyword

---

## **[March 14, 2025]**

SEOmonitor identifies seasonal keywords by looking for predictable patterns of search volume that repeat at similar times across multiple years.



## **How the System Works**



### 1. Data Collection and Preparation

- The system analyzes _up to_ 24 months (2 years) of search volume data
- It needs _at least_ 12 months of data to make a decision
- The data is organized by month to detect patterns



### 2. Establishing Thresholds

The system calculates two thresholds (one for each year of data):

- It finds the **median** (middle value) of the monthly search volumes
- It calculates the Median Absolute Deviation (MAD) to understand normal variation
- It applies a dynamic factor to the MAD (calculated using the chooseMadFactorDynamic method)
- The threshold is set as: `max(median+madFactor*MAD, 50)`
- The 50 value (minAbsolutePeak) ensures small-volume keywords aren't detected as seasonal due to minor fluctuations



### 3. Finding Seasonal Periods

- The system looks for consecutive months where search volume is at least 95% of the threshold
- These months form "segments" - potential seasonal periods
- For a segment to be valid, it must:
  - Last _at least_ 3 months (minSeasonLength)
  - Be _less_ than 8 months long (otherwise, it's considered year-round demand)
  - Not be part of more than 2 separate seasonal periods in a year




### 4. Comparing Patterns Across Years

- The system compares segments from the first year with segments from the second year.
- For segments to match, they must:
  - Start within 2 months of each other in each year (maxStartDiff parameter);
  - Have lengths that differ by no more than 2 months.




### 5. The Final Decision

- If matching seasonal patterns are found across two years, the system identifies:
  - The start month of the seasonal period;
  - The end month of the seasonal period;
  - Potentially a second seasonal period, if one exists.




## **How to Verify if a Keyword is Correctly Identified as Seasonal**

To check if the system correctly identified a keyword as seasonal:

1. Gather 24 months of search volume data for the keyword.
1. For each 12-month period:
  - Calculate the median search volume
  - Determine the typical variation (MAD)
  - Set a threshold that's either significantly above the median or at least 50 searches.

1. Identify periods where search volume exceeds or nearly exceeds this threshold for at least 3 consecutive months.
1. Check if these periods appear in similar months across both years.
1. If matching patterns are found that start within 2 months of each other and are of similar length, the keyword is correctly identified as seasonal.

This approach ensures that the system identifies genuine seasonal patterns while filtering out random fluctuations or one-time spikes in search interest.


## **The Three Seasonal States**

1. **In Season** (KW_IN_SEASON = 1)
  - This is when the current month falls _within_ the seasonal period
  - Example: If a keyword is seasonal from June (6) to August (8), and the current month is July (7), it's "in season".
  - Has the highest importance value (3)

1. **Approaching Season** (KW_APROACHING_SEASON = 0)
  - This is when the _next month_ will be the _start_ of the seasonal period
  - Example: If a keyword is seasonal from June (6) to August (8), and the current month is May (5), it's "approaching season"
  - Has medium importance value (2)

1. **Out of Season** (KW_OUT_OF_SEASON = 2)
  - This is when the keyword is neither in season nor approaching season.
  - Example: If a keyword is seasonal from June (6) to August (8), and the current month is October (10), it's "out of season"
  - Has the lowest importance value (1)




Shape-up here: [https://app.clickup.com/2179830/v/dc/22gqp-15507/22gqp-136972](https://app.clickup.com/2179830/v/dc/22gqp-15507/22gqp-136972)
Seasonality algorithm: [https://app.clickup.com/2179830/v/dc/22gqp-22832/22gqp-144112](https://app.clickup.com/2179830/v/dc/22gqp-22832/22gqp-144112)
