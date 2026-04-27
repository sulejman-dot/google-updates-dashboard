# Historical Ranks Import - expected behavior in SEOmonitor

> **Collection:** Customer Success
> **Last Modified:** 2019-06-21
> **Tags:** historical data, historical ranks, import ranks, Katty, migration

---

Importing historical ranks can be done 2 ways:

**Don't overwrite - ** data will be added where there is no info, provided that it's older than the date the keyword was added. Any info more recent than the date the keyword was added will be ignored.

**Overwrite **

- 
If there are values (0 included) the new info will overwrite the existing one (for the moment empty cases have the same behavior as 0)

- 
If there is historical data, no matter if imported or coming from SEOmonitor,  and a new import is made for a shorter period, the expected behavior is for the data to be overwritten only for that specific period, leaving the rest of the info intact, provided that above conditions are applied for the imported file..


*Subsequently to importing the historical ranks, the "date added" of the keyword will become the first day with data and "date added" for the campaign will become the first day for which a keyword has imported historical data.

**Imported historical ranks will overwrite any data, including SEOmonitor's
