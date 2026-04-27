# ​What are the Brand criteria for Topics?

> **Collection:** Customer Success
> **Last Modified:** 2019-04-19
> **Tags:** brand criteria, brand label, brand types, Mircea, non-brand keywords, site links, special brand, topics

---

In rezultatele din Topic Explorer intră doar cuvintele care au (site_links < 2).

Proprietatea site_links se stabileste în funcție de rezultatele de pe primele poziții din SERP și se clasifică astfel, iar prioritatea stabilirii valorii este în ordine:

- 
**NOT BRANDS**

- 
**site_links = 0** - primul rezultat nu conține decât titlu și descriere, fără alte briz-briz-uri


[https://api.monosnap.com/rpc/file/download?id=7gYSJS9Ni09rbGDCECF8Jb8CGHSBIc](https://api.monosnap.com/rpc/file/download?id=7gYSJS9Ni09rbGDCECF8Jb8CGHSBIc)

- 
**site_links = 1** - primul rezultat conține link-uri (mici), sub descriere


[https://api.monosnap.com/rpc/file/download?id=uypFmvYpTwKPm7kvxzH3n1vyT6OAMS](https://api.monosnap.com/rpc/file/download?id=uypFmvYpTwKPm7kvxzH3n1vyT6OAMS)

- 
**BRANDS**

- 
**site_links = 2 **- primul rezultat conține link-uri cu descriere (mari), sub descrierea rezultatului


[https://api.monosnap.com/rpc/file/download?id=Wxy78VFwWco5SntYe3UtzaYJlaDgUJ](https://api.monosnap.com/rpc/file/download?id=Wxy78VFwWco5SntYe3UtzaYJlaDgUJ)

- 
**site_links = 3** - primele 4 rezultate aparțin aceluiași domeniu


[https://api.monosnap.com/rpc/file/download?id=VjVAyJLdYWQs3pPdZm05t0w5xhDMpa](https://api.monosnap.com/rpc/file/download?id=VjVAyJLdYWQs3pPdZm05t0w5xhDMpa)

- 
**site_links = 4** - cuvântul conține un alt cuvânt cu site_links = 2, de exemplu "minifrigider emag" sau "raiffeisen carduri"

- 
**site_links = 5 **- cuvântul are primele trei rezultate aparținând aceluiași domeniu, plus un Knowledge Graph

- 
**site_links** **= 6** - cuvântul are un Knowledge Graph de unul din următoarele tipuri:

- 
Company

- 
Video Game

- 
**site_links = 7** - cuvântul are site_links = 1 și primele 2 rezultate aparțin aceluiași domeniu

- 


- 
**SPECIAL NOT BRANDS**

- 
**site_links = -2** - este un cuvânt care are site_links = 2, dar primul link nu e http://homepage.tld/, sau [http://homepage.tld/[2](http://homepage.tld/%5B2) litere]/ sau [http://domain.tld/[2litere]-[2litere]/](http://domain.tld/%5B2litere%5D-%5B2litere%5D/) - aici intră de obicei cuvinte cheie care desemnează produse, gen macbook pro, samsung galaxy, placa de baza asus, etc. dar si exceptii de genul "subliminal dex", "bucuresti iasi km", "cinema cluj", "facebook ajutor".
