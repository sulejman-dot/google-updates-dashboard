# How connecting GA4 affects the Forecast objective?

> **Collection:** Customer Success
> **Last Modified:** 2023-03-07
> **Tags:** Andreea, forecasting, ga4

---

When one connects the GA4 profile they can choose to start using the data from GA4 from the connect moment or reprocess historically the data. Depending if the data between the UA & GA4 match, it will not affect the historical data if the client chooses not to reprocess. 

Most likely the data will differ between the 2 profiles (sessions and transactions) because of the way GA4 is recording sessions, the forecast was based on the UA data so it will be differences in terms of the inertial data for the remaining months.
