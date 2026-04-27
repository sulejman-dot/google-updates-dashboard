# Additional Sessions in Opportunity, in the Rank Tracker, versus Additional Sessions in Forecasting

> **Collection:** Customer Success
> **Last Modified:** 2021-07-09
> **Tags:** additional sessions, analyze calculation, Delia, estimated sessions, forecast, OPP, Opportunity, top 3

---

If you compare the additional sessions once in top 3 estimated in the Opportunity Score: [https://take.ms/tPkaI](https://take.ms/tPkaI) to the additional sessions once in top 3 from the "Analyze Calculation" option in Forecast: [https://take.ms/Yb1ZQ](https://take.ms/Yb1ZQ) you will notice a different number between these sections.

- 
Additional Sessions in **Opportunity** only take desktop ranks (in Difficulty) into account. _--> they will be added into the export._

- 
Additional Sessions in **Forecast** also take into account the mobile search % and the CTR curve(s), and you can also include/exclude the year-over-year trend. _--> this is the more accurate measure_


Extra details: the Opportunity metric is computed as follows

```
`Opportunity = [Potential new monthly clicks] / [Difficulty to rank in Top10] `
```

where

```
`[Potential new monthly clicks] = Search Volume * [CTR(Top3)-CTR(current rank)]`
```
