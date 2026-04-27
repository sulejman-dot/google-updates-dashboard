# Data Studio - Why is there a 1K lines limit

> **Collection:** Customer Success
> **Last Modified:** 2022-01-19
> **Tags:** 1000 limit, data studio, Ioana, limit, line limit, lines, rows

---

Our APIs have certian limitations. We cannot request the database to bring 12K keywords at once, for example, because it will crash, so we have a limit of 1K keywords per call. 

But that's not of any concern for the user, because the Connector brings all the data eventually, just not everything at once. It first requests 1K, then the next 1K and so on till bringing everything.

This happens while the user sees the table as loading on their side. When the processing done, they will be provided with the full set of data.
