# SEO Opportunity Score with Explainer

> **Collection:** Customer Success
> **Last Modified:** 2023-02-01
> **Tags:** cup, opportunity score, score, stefan, trophy

---

newest Help article - [https://help.seomonitor.com/en/articles/6222130-seo-opportunity](https://help.seomonitor.com/en/articles/6222130-seo-opportunity)

---

It is a keyword-level metric that brings all the qualitative and quantitative attributes of a keyword in one metric that helps users sort their keywords based on the opportunity to start optimizing their website for them right now. It works as a percentile, taking values from 0 to 10, where 10 represents the top 10% and 1 represents the bottom 10%. The attributes are:

- 
Search Volume

- 
Year-over-Year Search Trend

- 
% of searches that end up clicking on an organic result (SERP features impact)

- 
CTR difference between the current rank and Top3 

- 
Difficulty of the website to rank in top 10


**How it works: **

- 
The metric is calculated real-time and uses all the keyword attributes in SEOmonitor to process 2 key metrics:

  - 
Potential new monthly clicks when reaching Top 3

  - 
Difficulty to rank in top 10


- 
Potential new monthly clicks =(CTR[1-3] - CTR[current_rank]) * avg_search_volume * YoY * %clicks_on_organic

- 
Opportunity Score = Percentile([Potential new monthly clicks] / [Difficulty to rank in Top10])/10 - calculated relative to all keywords in the campaign


**Anything else about it:**

- 
It is also processed at a keyword group level.

  - 
Group Opportunity Score:  average(Opportunity Score)


- 
The metric has an explainer that describes the Difficulty metric value and the

  - 
Estimated additional Sessions, Conversions and Revenue when reaching the top (if Analytics is connected)

  - 
Estimated additional Clicks when reaching the top (if only GSC is connected)


- 
The Opportunity score is not calculated for misleading keywords with warning label:  brands of others, irrelevant keywords, highly localized keywords -> N/A with tooltip

- 
The Opportunity Score for keywords already in Top 3 is 0, as there's no more room to grow, and it is highlighted with a Trophy icon.
