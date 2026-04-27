# Can we influence Google Trends through rank tracking?

> **Collection:** Customer Success
> **Last Modified:** 2026-02-27
> **Tags:** GSC, ranks

---

We can't meaningfully influence Google Trends through rank tracking.

  Here's why:

  1. Scale mismatch: Google processes billions of searches per day. Even if SEOmonitor tracks hundreds of thousands of keywords daily, that's a rounding error in Google's total search volume. Google Trends shows relative interest normalized across all searches — our volume wouldn't move the needle.

  2. Google Trends filters bots: Google explicitly states they filter out "repeated queries from a single user over a short period of time" and automated/bot traffic from Trends data. Our rank tracking queries come through proxy infrastructure with patterns (systematic querying, no clicks, no follow-up searches) that are trivially identifiable as non-human.

  3. The queries aren't "real" searches: Our rank tracking goes through an internal proxy swarm (monse6-wg.internal) that rotates IPs and handles bans. Google is already well aware this is automated traffic — that's why they rate-limit and ban IPs. Traffic they're actively fighting isn't being counted in Trends.



 In summary, Google Trends data is not affected by rank tracking tools, and at most we could generate around 10 impressions per keyword.
