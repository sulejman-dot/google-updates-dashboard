# How do the rank & rank change filters work?

> **Collection:** Customer Success
> **Last Modified:** 2019-06-13
> **Tags:** filters, Mircea, rank change

---

**Rank filter**

- 
expected behaviour: rank higher than 4 = better ranks than 4 (1,2,3), not mathematical


**Rank change filter**

- 
Expected behaviour:


**Rank change **- the operator functions mathematically; example  [`rank change` < 4], we will display changes from 4 downwards to - ∞ 

**Rank change (absolute)** - filtrarea se intampla pe valoarea absoluta a change-ului; ex.: filtrul [`rank change` < 4] o sa contina change-uri intre -3 si 3

to be updated - marius:  @cosmin Te rog sa-mi confirmi daca filtrele trebuie sa fie strict mai mici/mari ( > | < ) sau mai mici/mari si egale ( >= | <= )

Special situation - **smart groups filter with rank change - **for smart groups, we cannot, mathematically, show the entire interval changes, due to their volatile nature; the results will show the change from 30 days prior-to-the-current-day to the current day
