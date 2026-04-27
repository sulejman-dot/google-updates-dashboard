# ​Historical data from large files

> **Collection:** Customer Success
> **Last Modified:** 2020-04-13
> **Tags:** Ana, historical data, migration

---

Large files meaning that they exceed our bossulica limit of 115 MB.



- 
cum backblaze are o limita de 500 mb de upload, trebuie urmati pasii de aici, a.i sa se poata urca fisiere >500mb
`https://www.backblaze.com/b2/docs/quick_command_line.html`

- 
dupa ce se instaleaza pachetul de acolo, se pot da urmatoarele comenzi intr-un terminal:
- export LC_ALL="it_IT.UTF-8"- b2 authorize-account abc2477878fa 002d45a7cf62a775457cd48fdc9591377d12809efc- b2 upload-file rank-imports {caleFISIERdincalculator} {numeFISIERcumSAseNUMEASCAinBackBlazaDupaUpload}

- 
dupa ce se urca fisierul in backblaze: se acceseaza [imports.seomonitor.com/smadmin](http://imports.seomonitor.com/smadmin) (in loc de [app.seomonitor.com/smadmin](http://app.seomonitor.com/smadmin)).

- 
te loghezi normal in bosulica, ca si cum ai face-o de pe app.

- 
pe `imports.seomonitor.com` nu ar trebui sa primesc 500 de la cloudflare . Poti primi 500 de la serverul nostru daca ajungi in limita de memorie






PS: the details are from here: [https://trello.com/c/h8191o8y](https://trello.com/c/h8191o8y) 

CS info only The credentials to backblaze are: 

[https://secure.backblaze.com/user_signin.htm?netid=1570800367477](https://secure.backblaze.com/user_signin.htm?netid=1570800367477)

Email: [marius@seomonitor.com](mailto:marius@seomonitor.com)

Pass: L@4NA#ivZ9
