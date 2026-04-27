# Google Analytics URLs & compatibility with Analytics 360

> **Collection:** Customer Success
> **Last Modified:** 2022-10-05


---

Yes, any type of Analytics profile can be connected within the app, including 360.
It just needs to contain the corresponding data and to follow the general cross-check criteria:

Please make sure to associate the exact GA profile as the site URL that you've added to the application.
You should be cross-checking with the two below:

- 
Admin >> Property >> Property Settings >> Default URL

- 
Admin >> View >> View Settings >> Website URL


This way you make sure, that your campaign is set correctly.

---

Ad-hoc queries of your data are subject to the following general thresholds for sampling:

- 
Analytics Standard: 500k sessions at the property level for the date range you are using

- 
Analytics 360: 100M sessions at the view level for the date range you are using


Information from [Analytics Help](https://support.google.com/analytics/answer/2637192?hl=en)

---

Extra info: _When you approach the 10-million-hit limit, Google Analytics starts to warn you and offers a few options to resolve the situation:_

- 
_Buy Google Analytics 360;_

- 
_Send fewer hits;_

- 
_Perform app tracking using Google Analytics for Firebase (or switch to Event tracking using the beta version of _[Google Analytics App + Web](https://blog.google/products/marketingplatform/analytics/new-way-unify-app-and-website-measurement-google-analytics/)_)._


---

Note: From the info received so far, we don't differentiate the 2 profiles when connected to a campaign, and in Organic Traffic the warning is for 10 M hits / month.
