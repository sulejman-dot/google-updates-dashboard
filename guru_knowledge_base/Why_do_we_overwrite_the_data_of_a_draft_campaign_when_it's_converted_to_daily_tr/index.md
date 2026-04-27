# Why do we overwrite the data of a draft campaign when it's converted to daily tracking?

> **Collection:** Customer Success
> **Last Modified:** 2024-06-17
> **Tags:** data in draft, data owerwrite draft, draft, draft to tracking, Ioana

---

Because of a failsafe mechanism, "when a campaign is added after the daily rank crawling start (6 AM on their timezone), we also write ranks for the next day." This can lead to us displaying 2 days of data in a draft.

More shaping is in the making; see [here. ](https://app.clickup.com/t/8693hqy4x)
Another related task [here](https://app.clickup.com/t/8692pmz11)
