# ​Historical data imported by error - CS only

> **Collection:** Customer Success
> **Last Modified:** 2019-11-06
> **Tags:** Ana, historical data, migration

---

One solution used to be to overwrite the data by adding value 0 in a file. 

Recent task confirmed that this is not a solution:  valoarea `0` pentru rankuri intr-un import nu suprascrie deloc rankul existent, chiar daca tu ii dai optiunea de `overwrite` din interfata. E ca si cum rankul nu ar exista pe periaoda aia (asta inseamna valoarea `0`)

Any future cases are To be discussed on point with the Dev team.
