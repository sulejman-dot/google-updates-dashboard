# Why is there a discrepancy between the GA4 and traffic in the revenue metric? 

> **Collection:** Customer Success
> **Last Modified:** 2025-02-05
> **Tags:** ga4, metrics, revenue, traffic

---

Users may notice a discrepancy in conversion value (revenue) between the platform and GA4 when using the "Goals" conversion type in their traffic configuration settings.

This occurs because GA4's API does not allow revenue to be fetched by individual events when "Goals" is selected. Instead, it pulls the total revenue from all events, which may not align with the user's expected revenue data.

To get more accurate revenue tracking, users should consider switching to the "E-commerce" conversion type. This setting aligns with GA4’s 'purchaseRevenue' metric, which Google defines as:

"The sum of revenue from purchases minus refunded transaction revenue made in your app or site. Purchase revenue sums the revenue for these events: purchase, ecommerce_purchase, in_app_purchase, app_store_subscription_convert, and app_store_subscription_renew. Purchase revenue is specified by the value parameter in tagging."

By using "E-commerce" as the conversion type, users will see revenue data that better reflects purchase-related transactions, ensuring a more accurate comparison between the platform and GA4.
