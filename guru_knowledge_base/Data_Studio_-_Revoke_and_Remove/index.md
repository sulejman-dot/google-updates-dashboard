# Data Studio - Revoke and Remove

> **Collection:** Customer Success
> **Last Modified:** 2020-05-22
> **Tags:** Ana, data studio

---

Daca autorizezi un connector ii autorizezi pe toti, daca ii dai remove access din google account, le dai la toti remove.

best practice este sa ii dai revoke access din data studio. rapoartele care foloseau data sources create cu acel connector nu vor mai functiona. daca dai din nou pe el, nu o sa mai trebuiasca sa il conectezi cu accountul dar va trebui sa ii bagi api key.



((( "Autorizarea unui conector, implicand autorizarea tuturor, inseamana ca ulterior, chiar daca nu s-a creat raport cu ei, ar trebui sa apara Revoke access?" -> da. ii apare revoke acces

"Revoke access apare la fiecare conector doar dupa ce s-a dat Remove permissions?" -> nu. apare dupa ce il autorizezi

"Sau e afisat dupa ce s-a creat minim un raport?" -> apare dupa ce il autorizezi

"sau acest acces se refera la utilizarea unui API key? si nu neaparat adaugarea conectorului la data sources?" -> nu inteleg exact ce ma intrebi aici. autorizezi un connector. connector pe care il folosesti la un data source. )))



Se poate (12% sigur) sa aiba 2 connectori pentru ca a creat unu cu publish direct din script. Connector care practic este seaprat de cel pe care il acceseaza din "Partner connectors".
