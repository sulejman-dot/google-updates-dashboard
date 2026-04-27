# SERP download expected behaviour on the client side - INTERNAL PURPOSE ONLY

> **Collection:** Customer Success
> **Last Modified:** 2025-04-09
> **Tags:** Ioana, M test, SERP, SERP date, serp download

---

NOT TO BE SHARED WITH THE USERS


First, we attempt the day they want (aka current day), let's say the 28th. 
We try to validate that the position on that SERP matches with our DB and what they see as the latest position. 

If not, we move to the previous day, in our case, 27. 
If nothing is available, we move down all the way to the 23rd, attempting to find a matching SERP. 
If we don't have anything for the previous day, we then try to validate the next day, in our case, 29.

So, in extreme case when the client might end up getting tomorrow's SERP, it should actually match what they see in the platform. 

*From [this](https://app.clickup.com/t/8698hxv0c) task.
