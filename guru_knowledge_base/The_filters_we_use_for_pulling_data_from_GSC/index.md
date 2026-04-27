# The filters we use for pulling data from GSC

> **Collection:** Customer Success
> **Last Modified:** 2021-11-30
> **Tags:** filters, GSC, GSC clicks, Ioana

---

THERE IS A VALIDATION ONGOING HERE FOR THE NUMBER OK KEYWORDS IN GSC WHEN CHECKING WITH SPLIT BY LANDING PAGE AND DAY

We take the data from GSC differently and apply some filters:

- 
aggregation type - by page

- 
filters ignore pdf


If the filters removed the data comes identically like in GSC.

We ignore the indexed pages from with .pdf extensions from GSC because they will not have any match in Analytics, you cannot have tracking on those pages. 

The code for filtering for the GSC call: 
`{"startDate":"2021-10-01","endDate":"2021-10-31","dimensions":["query","page"],"aggregationType":"byPage","dimensionFilterGroups":[{"filters":[{"dimension":"page","expression":".pdf","operator":"notContains"}]}],"rowLimit":5000,"startRow":0}`
