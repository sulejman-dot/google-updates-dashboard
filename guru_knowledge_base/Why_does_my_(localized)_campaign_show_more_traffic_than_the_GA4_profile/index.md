# Why does my (localized) campaign show more traffic than the GA4 profile?

> **Collection:** Customer Success
> **Last Modified:** 2025-12-02
> **Tags:** analytics, ga4, Ioana, traffic, traffic inconsistency

---

Google Analytics recently implemented data threshold in their interface. This results in limited access to data in a report or exploration.
Data thresholds are applied to prevent anyone viewing a report or exploration from inferring the identity or sensitive information of individual users based on demographics, interests, or other signals present in the data.

**The data we display comes from Google Analytics API**, where they provide the full numbers; this is the reason why the numbers look like they do not match.

So it looks like your options would be:

- implement in your GA profile the different [indications offered](https://support.google.com/analytics/answer/9383630) by Google's support
- try to create different GA views by country, in case you opted for localized traffic in your campaign.

[Here](https://app.getguru.com/card/iR9ynK5T/How-to-check-traffic-in-Google-Analytics) is the info regarding how to make the checks in GA.

____________________________________________________________________________________________

**Internal info. Do not share this directly with the client**


[This](https://stackoverflow.com/questions/75723392/google-analytics-4-is-summing-sessions-incorrectly-why [https://stackoverflow.com/questions/75723392/google-analytics-4-is-summing-sessions-incorrectly-why]) is an accurate and realistic explanation.


_Because the main idea behind GA4 is for Google to save money on servers dedicated to supporting Analytics. Frankly, GA UA used to be too good for a free product._
_..._
_In other words, plain simple summing might be too expensive for GA4 to conduct in that report, so it uses advanced algorithms that do sums faster, but less accurate._

---

Related:

- [Why do you sometimes see a different number of clicks compared to GSC when selecting a longer timeframe? (also applies to GA sessions)](https://app.getguru.com/card/iaBog8dT/Why-do-you-sometimes-see-a-different-number-of-clicks-compared-to-GSC-when-selecting-a-longer-timeframe-also-applies-to-GA-sessions)
- [Understand how sampled data can affect your campaign](https://app.getguru.com/card/9ieyzEpi/Understand-how-sampled-data-can-affect-your-campaign)
