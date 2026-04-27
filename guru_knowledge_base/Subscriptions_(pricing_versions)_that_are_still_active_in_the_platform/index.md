# Subscriptions (pricing versions) that are still active in the platform

> **Collection:** Customer Success
> **Last Modified:** 2024-06-28
> **Tags:** build measure, grandfathered, grandfathered pricing, grandfathered subscription, Ioana, new pricing, old pricing, Pricing, pricing versions, simple pricing, subscriptions

---

We currently have clients for which the following pricing versions are active, each with their particular rules listed below.
Besides **Build-Measure**, all other options are grandfathered, and no new customer has access to them. 

1. "[**Old Subscription**](https://app.seomonitor.com/custom_pricing)" - the minimum value for this type of subscription is €49
It's applicable to users that have `old_subscription` flag enabled **OR** created before `2020-11-13`
  1. min. 300 keywords
  1. base price/keyword = €0.13*
  1. all regular campaigns are billed, even those without GSC connections. The price is €10/campaign

1. "**New Subscription**" -  the minimum value for this type of subscription is €198
In between "Old Subscription" and the new types (simple/build-measure) - this applies if no other rule matches:
  1. min. 4k keywords
  1. base price / kw = 0.047*
  1. all regular campaigns are billed, even those without GSC connections. The price is €10/campaign

1. "[**Simple Pricing**](https://app.getguru.com/card/TEgAEgzc/Simple-pricing-calculator)" - the minimum value for this type of subscription is €149.50 (initially "sold" as $ to clients)
Applies to users created after `2022-10-01`  **OR** manually flagged with `simple_pricing=1`:
  1. min. 5k keywords
  1. Keywords are billed in 1k batches - at €29.9/1k
  1. only campaigns with GSC connected are billed. The price is €9.99/campaign

1. "**Build-Measure**" - it's a "Simple Pricing" type of subscription with additional rules and applies to users having the `is_measure_build` flag enabled:
  1. €99 base price - give access to the Build version of the tool (unlimited number of draft campaigns)
  1. min. 0 keywords (overrides the simple pricing limit)
  1. usually, users having this flag should also have `simple_pricing` enabled so that the rest of the simple pricing rules apply

1. "**Build-Measure**" - same description as above, but starting with 09.04.2024, the price per 1000 keywords is €39
1. "**Build-Measure**" - same description as above, but starting with 30.05.2024, the price per 1000 keywords is €47
  1. starting 07.06.2024 there's a 3000 kw minimum, so they all **start at €240/month** now (= €99 + 3*€47).





*For **non-Simple Pricing** accounts, the base price/keyword decreases with volume - as listed here: [https://docs.google.com/spreadsheets/d/1ByPzX0xjYvH09UBo964YmIrlLeEttiyTFtS21Nm4Oug/edit?usp=sharing](https://docs.google.com/spreadsheets/d/1ByPzX0xjYvH09UBo964YmIrlLeEttiyTFtS21Nm4Oug/edit?usp=sharing)
