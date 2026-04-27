# Understanding CPC data at a KW level

> **Collection:** Customer Success
> **Last Modified:** 2020-07-16


---

**Issue - KWs are missing CPC or how do we check if the CPC cost is correct?
 **[https://take.ms/p7dRv](https://take.ms/p7dRv) - app view
 [https://take.ms/aU0JCX](https://take.ms/aU0JCX) - KW planner

Customer use case: 
Keywords are missing their CPC cost and the [Media Value](https://app.getguru.com/card/ca9aLa7i/Media-value-display?q=media%20value) is very low for the account.

Customer response:
Google Adwords has updated its interface and it no longer shows the Avg CPC cost but a min and max. They also have an API that is currently in Beta. We are still using the OLD API which for some keywords does return an AVG CPC cost however it also returns "null" values. There are a few reasons why the API would return null: the KW has a very few searches and far between which no potential for an Ad campaign or a very niche term that does not return values.
