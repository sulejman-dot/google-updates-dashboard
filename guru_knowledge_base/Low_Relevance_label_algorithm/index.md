# Low Relevance label algorithm

> **Collection:** Customer Success
> **Last Modified:** 2022-04-15
> **Tags:** Ioana, low relevance, low relevance algorithm, low relevance label, relevance, relevance label

---

The calculation of keyword relevance happens **only when adding the keyword**, and it is based on the set of existing competitors.

If the keyword is** added when the campaign is created**, the competitors on which the relevance metric is based, are the initial competitors of the campaign. (check here for more details: [https://app.getguru.com/card/TaKxAgyc/The-Low-Relevance-Label?q=relevance](https://app.getguru.com/card/TaKxAgyc/The-Low-Relevance-Label?q=relevance))

The algorithm is as follows:

- 
we set the max relevance value, which is equal to `21 * number of competitors + 1`

- 
we calculate the relevancy for the keyword which is `number of competitors * 21 - sum(21 - keyword rank on competitor/2)`

  - 
if the competitor rank is >= 21, then the relevance score is maximum


- 
We calculate the percentage by doing `kw relevance/max relevance`

- 
the value is saved on the keyword database entry.

- 
in the interface, the low relevance label is applied if all following conditions are true:

  - 
relevance percentage > 0.92

  - 
latest rank > 20

  - 
best rank > 20

  - 
keyword is "main" or not aggregated



**
-EXAMPLE-**

Let's assume we have 1 keyword that we just added, and a pool of 3 competitors on which we want to calculate the relevance. The keyword's ranks on each competitor are : my_site ➝ 19, comp1 ➝ 15, comp2 ➝ 36, comp3 ➝ 99+

- 
We pull the competitors and calculate the max relevance score which is `21 * (competitor count + 1) = 21 * (4 + 1) = 105`

- 
The formula for the keyword's low relevance score is as follows

  - 
`competitor count * 21 - sum(21 - [rank/2 or rank or 21])` - we use rank/2 if it is my site, 21 if it is my site and rank >= 21 and rank if it is not my site

  - 
In this case, we need to do the following:

    - 
`4*21 - [(21 - 19/2) + (21 - 15) + (21-36) + (21-100)] = 106,5`



- 
We calculate the percentage

  - 
the value above/max_relevance - in this case: `106.5/105 = 1.01`


- 
If percentage > 0.92 and latest_rank > 20 and best_rank > 20 and the keyword is not a child in an aggregation group, then the low relevance label is applied.
