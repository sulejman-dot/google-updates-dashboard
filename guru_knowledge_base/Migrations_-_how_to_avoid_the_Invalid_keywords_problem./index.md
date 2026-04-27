# Migrations - how to avoid the Invalid keywords problem.

> **Collection:** Customer Success
> **Last Modified:** 2022-01-26
> **Tags:** Delia, invalid keywords, migration, migration invalid keywords, parsed

---

The "invalid keywords" issue appears when the data exported from the other tool is not encoded as UTF-8.
Even if you later save it as a UTF-8, the original CSV not saved correctly from the other tool will cause this issue because it will double some special characters that cannot be noticed in a larger pool of keywords.

**We now have a new checkbox in the Migration Tool wizard on step 1 (Keyword Column). It is named "Convert UTF8 to Win1252" and if checked it will perform one additional operation on the keywords text fixing this exact issue.**

- 
**THERE'S NO WAY TO TELL IF IT'S CORRECTLY SAVED BUT IF WE GET THE INVALID KEYWORDS ERROR IN THE PARSED FILES WE CAN APPLY THIS CHECKBOX**


****

DO NOT USE THIS CHECKBOX FOR REGULAR CSVs AS IT MIGHT AFFECT THE ENGLISH CHARACTERS.
