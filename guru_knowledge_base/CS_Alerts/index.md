# CS Alerts

> **Collection:** Customer Success
> **Last Modified:** 2019-04-23
> **Tags:** alerts

---

Don’t assign them to you. Add an internal note, do what needs to be done, close them.

[Sheet 4](https://drive.google.com/a/bunt.ro/file/d/0B6n1iCQYStd2YmltaElLSWxQbWM/view?usp=sharing)

1. 
**GWT Access (GSCImpressionSplit / new parser) revoked for site: “site-name” (# site id - number )**

  1. 
Check account for “site-id - number”

  1. 
Check Web settings 

  1. 
Check GSC for the site or “site-id - number” (for many campaigns) if it’s connected 

  1. 
If GSC is not found, send email to owner/user

  1. 
Add note with status in IC

  1. 
Close alert in IC 


1. 
**GA Access revoked for site: “site-name” (# site id - number )**

  1. 
For user “upswing” inform the person from “upswing”

  1. 
Close the alert in IC

  1. 
Check account for “site-id - number”

  1. 
Check Web settings 

  1. 
Check GA for the URL site if any error or warning is shown

    1. 
Check the site - View settings - exact GA ID


  1. 
If GA is not found, send email to owner/user

  1. 
Add note with status in IC

  1. 
Close alert in IC 

  1. 
If no “site-id - number” is found in app - check full story (it’s possible that the owner deleted the campaign)


1. 
**Best Topic Explorer DB different from tld for ”site id - number”**

  1. 
Check account for “site-id - number”

  1. 
Check “Discover (Research)” for details of campaign configuration

    1. 
Just as double check: see keywords


  1. 
Check Full story to see how the owner set up the campaign

    1. 
If campaign set up global and should be localized: involve sales - send email with owner and site details and afterwards close the alert in IC

    1. 
If campaign set up correctly: close alert in IC


  1. 
Close the alert in IC


1. 
**Exact GA profile not found for SID:”number”**

  1. 
Check account for “site-id - number”

  1. 
Check GA data

  1. 
Check URL site added by the client

  1. 
If GA and URL don’t match, send email/in app (message in IC) to client advising to connect the correct profile. Afterwards close the alert in IC

  1. 
Deleted? 


1. 
**[ALERT] Brand / Non-brand change: “site-name” (# site id - number )**

  1. 
Check account for “site-id - number”

  1. 
Check “Understand (Organic Traffic)” for a larger period of time (all keywords, Split Brand and Non-Brand view)

    1. 
Check Landing Page

    1. 
Check GA data for the exact dates of brand/non-brand switch dates

    1. 
If needed, also check GSC for the exact dates of brand/non-brand switch dates

    1. 
Connect GSC with Landing Page with unallocated traffic

    1. 
Add details in Brand/Non-brand document in Google Drive

    1. 
Close the alert in IC

    1. 


      1. 
Go on All keywords in Organic Traffic.

      1. 
Split brand/non-brand.

      1. 
Scroll in the calendar all the way back to the switch(es).

      1. 
Switch on to LP view.

      1. 
Analyse what it looked like before and after the switch (check on one day, in both situations




1. 
**Re-engage GA connected wizard not finished**

  1. 
Check account for “site-id - number”

  1. 
Bypass the system using “/my_account/subscription_details”

    1. 
Skip “connect GSC”

    1. 
Add competitors (1 or 2)

    1. 
Add keyworkds (from TE or best from site)

    1. 
Finish wizard 


  1. 
Sent email to owner/user

  1. 
Close the alert in IC


1. 
**[Site in progress alert] Progress delayed 1 hour**

  1. 
Check account for “site-id - number”

  1. 
Check “Understand (Organic Traffic)” for traffic

  1. 
Check “Manage (SEO Campaign)” for all kw data to be done

  1. 
If still in processing (either OT or SEO campaign) - create task

  1. 
Close the alert in IC


1. 
**SM App Subscription Error - Limits exceeded!**

  1. 
Usually for accounts with set up limit

  1. 
Check account for “site-id - number”

  1. 
Check number of keywords used (in Settings and SEO Campaign)

  1. 
If the number is: 

    1. 
A total of brand + non-brand, than it’s a fake error

    1. 
Exceeded: am email is sent to owner/user 



1. 
**Cancel Subscription Reason for User : “e-mail address”**

  1. 
Check details about campaign/user

  1. 
Sent an email to owner/user asking for feedback (if applicable offer/apply Promo Credits)

  1. 
Add note in IC

  1. 
Close the alert in IC


1. 
**Blocked Manage Site # site id - number - {"site_id":number, "data": ""}**

  1. 
Check account for “site-id - number”

  1. 
Check “Understand (Organic Traffic)” 

    1. 
If it’s an old site: add Trello task with check list, also add full story details -> add note with Trello task in IC

    1. 
If it’s a new site: no action is needed


  1. 
Close the alert in IC


1. 
**Hard bouncers**

  1. 
Can be: 

    1. 
Email address that are no longer valid

    1. 
Users that left the company. In this case sent an email to the owner

    1. 
Fake users. In this case send a message in app


  1. 
Close the alert in IC


1. 
**Failed payment or closed account due to exhausting the 5 attempts to pay an invoice (via slack).**


a. Check the reason for failing, in Chargebee.

b. Only at the second failed payment alert, you write to the email address from the alert (or if we know some of the members working there - users that we had interaction via email or Intercom, we add their email as well), containing all the necessary info (cause of failed payment, when is next payment & reminder of automatically closing account at 5 failed attempts).

c. If the account got closed:

       i. Write to them for feedback (check before if they left any comment in Chargebee and see from there on), ask if there is any feature missing (+ Product portal) & if they need help with exporting data from the account.

      ii. If you need to reactivate the account, you email them to confirm the account is active, with the new/current invoice attached, to make sure they have it + if's the case, the new expected payment date (or until when the dunning was paused).
