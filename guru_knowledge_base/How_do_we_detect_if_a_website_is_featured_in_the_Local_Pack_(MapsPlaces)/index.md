# How do we detect if a website is featured in the Local Pack (Maps/Places)

> **Collection:** Customer Success
> **Last Modified:** 2024-04-25
> **Tags:** algorithm, Ioana, local pack, maps, maps pack, places

---

First, if the Maps/Places result has a link, it has to match the campaign's URL.


For results without links, we're using the result title going through this algorithm:

- Curation for the result title
  - Remove all non-alphanumeric characters
  - Remove words with <= 3 characters

- We then split the title into individual words, and we count how many are included in the campaign's domain name
- We consider the campaign as featured if:
  - The concatenation of the title words exactly matches the domain name
  - OR more than 75% of the title words are contained in the domain name (but no less than 2)



IF the above algorithm doesn't match, there's a secondary fallback -> if the campaign homepage title contains the exact same words as the Places/Maps result's title.


*The site's homepage can be checked by hovering over the tab when accessing the tab in the browser.



from [https://app.clickup.com/t/8694778dw?comment=90120035149417](https://app.clickup.com/t/8694778dw?comment=90120035149417)
