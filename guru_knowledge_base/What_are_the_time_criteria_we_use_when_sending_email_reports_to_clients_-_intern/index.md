# What are the time criteria we use when sending email reports to clients? - internal info

> **Collection:** Customer Success
> **Last Modified:** 2023-05-19
> **Tags:** Delia, email, email reports, monthly report, weekly report

---

A scheduled task runs every day at a fixed time and goes through all the active campaigns. it checks each and every one of them and decides if it needs to send a weekly or monthly report for them based on their settings and the current date. 

The list of campaigns is not ordered explicitly, so it's arbitrary.  These are intensive processes, so they get sent when they're ready for all the campaigns and all the clients.



In conclusion, we cannot reliably predict when a report will be sent during the execution of the scheduled event.
