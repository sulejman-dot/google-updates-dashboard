# Granularity of Competition Visiblity for Data Studio calls

> **Collection:** Customer Success
> **Last Modified:** 2023-04-05
> **Tags:** Competition, competition visibility, competitor, competitor visibility, data studio, Ioana, visibility

---

VS Competition connector automatically pulls:

- 
daily for timeframes up to 31 days

- weekly for timeframes between 31 and 99 days - last day of the week
- monthly for time frames higher than 99 days - last day of the month

Because of this behavior, if you select 1 year, the graph will look all spiky, as it will only have values for the 1st of each month. In order to make it look smoother, you will have to edit the Date simension, at select "Year Month"
[https://take.ms/lLjjZ](https://take.ms/lLjjZ)
