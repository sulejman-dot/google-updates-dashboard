# Estimated additional traffic - Landing Page Opportunity vs Keyword Opportunity

> **Collection:** Customer Success
> **Last Modified:** 2023-09-11
> **Tags:** additional traffic, estimated additional traffic, Ioana, landing page, landing page additional traffic, landing page opportunity, LP opportunity

---

**Keyword Opportunity formula** 

_opportunity_ = est_traffic/difficulty

_est_traffic_ = (CTR[1-3] - CTR[current_rank]) * AvgSearchVolume * YoY * %ClicksOnOrganic

**Landing Page Opportunity**

_LP_opportunity_new_ = sum(kws_opp_new) * nr days in period[​
](https://seomonitor.slack.com/archives/D1QECA275/p1616423314001500)kw_opp_new, is not the 0 si 10 opportunity, it's an intermediate value used to calculate that score

_LP_est_traffic_ = LP_opportunity_new * LP_difficulty_new

Example
For **https://wordfinder.yourdictionary.com/scrabble-dictionary/ ** there are 2 keywords that are ranking[​
](https://seomonitor.slack.com/archives/D1QECA275/p1616423334001700)**scrabble dictionary - (id=**5649985) -> opp_new = "5793.3"
**scrabble helper - (id=**5649983) -> opp_new = “0” 
nr days in period = 28
LP_opportunity_new = (5793.3 + 0) * 28 = 162212,4 
LP_difficulty_new = 1
so
LP_est_traffic =162212,4

Code details (internal use only) [https://docs.google.com/document/d/1JE5ZFwnRNkagpWOUG0qTPY1K5yh5YZclJQYpqr4r-Nk/edit?usp=sharing](https://docs.google.com/document/d/1JE5ZFwnRNkagpWOUG0qTPY1K5yh5YZclJQYpqr4r-Nk/edit?usp=sharing)
