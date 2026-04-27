# Why are there more options for granularity for the Visibility Score in Competition?

> **Collection:** Customer Success
> **Last Modified:** 2024-08-14
> **Tags:** Competition, granularity, Ioana, sampling, visibility, visibility score

---

The sampling in Competition is an old decision. And it was made to give the user a good-enough granularity while keeping a good loading speed. **(don't share with the client the whole phrase)**

There’s a big difference between Strategy, where we only provide daily granularity, and Competition. The first one has just one website plotted, while the other one has up to 10. It would also be a mess with a chart that has 10 lines with hundreds of dots each. 

One more thing, sampling is not averaging. We just take one day out of 7 (when doing weekly sampling) and one day out of 30 (when doing monthly sampling), more precisley, the Visibility is displayed:

- daily for timeframes up to 31 days
- weekly for timeframes between 31 and 99 days - last day of the week
- monthly for time frames higher than 99 days - last day of the month
