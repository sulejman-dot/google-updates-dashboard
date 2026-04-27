# Algorithm for MISSPELLING label

> **Collection:** Customer Success
> **Last Modified:** 2021-05-21
> **Tags:** algorithm, Ioana, misspelling, misspelling algorithm

---

Automatically applied to the keywords where the search returns one of the messages (verifiable in the SERP):
- did you mean: ...
-  showing results for...

For the rest, the following steps are made:
1. the keyword is split in individual words 
2. every individual word is searched for in title and description, all through the Top100 results.

If none of the individual words is identified in any of the results, the keyword is marked as Misspelling.
