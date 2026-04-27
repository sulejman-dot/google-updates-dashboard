# Why do we see differences between the CTR in OT and the one in GSC?

> **Collection:** Customer Success
> **Last Modified:** 2024-11-04
> **Tags:** CTR, Delia, GSC, gsc export, organic traffic

---

Although our CTR (in Organic Traffic) and Google Search Console (GSC) CTR share the same name and reflect similar behaviour, they are calculated differently, so their values may not match.

The GSC CTR is defined as clicks divided by impressions based on the data shown in GSC. For more details on how GSC calculates CTR, you can refer to their [documentation](https://support.google.com/webmasters/answer/7576553?hl=en#choosingmetrics). 


Our CTR, however, is calculated using data we collect during our "not provided" distribution process. The key differences are:

1. We do not store data for rows with 0 clicks.
1. Our data is pulled from the keyword breakdown by landing page per day. This approach can result in different values compared to the keyword view in GSC, even if you try to recalculate the metrics in GSC.
