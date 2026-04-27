# LP Override (subdomain with main domain)

> **Collection:** Customer Success
> **Last Modified:** 2020-12-16
> **Tags:** Alex, LP, LP override

---

We have the option to override the LPs in the Admin Section of the Account Settings
in LP Override you can use the following formula:  replace-domain:domain_to_replace.com:new_domain.com

Example: replace-domain:quote.salongold.co.uk:salon.gold.uk
The above example allows us to distribute the sessions from the subdomain (quote.etc) in the main domain.

We can extend the override to multiple domains as well.
a: subdomain 1
c: subdomain 2
b: main domain

Example: replace-domain:a:b, replace-domain:c:b
