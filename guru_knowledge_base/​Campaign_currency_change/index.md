# ​Campaign currency change

> **Collection:** Customer Success
> **Last Modified:** 2021-02-26
> **Tags:** Alex, Ana, currency

---

As admin, from din website settings you have the option to change two currency options:

- Analytics currency - doesn't change the numerical values, and doesn't calculate the conversion in that currency (it is just a display setting)

- AdWords currency - changes only the currency of AdWords data (CPC) and starts a data reprocessing of AdWords data for all the keywords from the campaign. 

PS: There is not need to reprocess the data (the actual options in red from the admin section) 

LATER EDIT:

The currency must be changed in both fields to the appropriate currency acronym (Dollars = USD / Pound = GBP)
Pitching campaigns without GA are automatically set to EURO (adding a GA to them will have the currency overriden with the currency present in analytics)
Normal campaigns (and converted pitching campaigns with GA) automatically pull the currency from the GA (if we manually update the currency, on the next analytics update it will revert back the currency)
