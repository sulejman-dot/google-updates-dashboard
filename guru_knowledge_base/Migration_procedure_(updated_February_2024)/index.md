# Migration procedure (updated February 2024)

> **Collection:** Customer Success
> **Last Modified:** 2024-03-11
> **Tags:** Delia, email, Maria, migration

---

**SLA**: 7 days max

Most recent duration [estimates](https://docs.google.com/document/d/1yhk-kjxalrSUOoim3qDxeFz7T2DyJ9WsSK-F_JVpWqo/edit?usp=sharing) (Feb'24) at CS:

- 5' / campaign for the migration
- 3' / campaign for the checks

Most recent **tracker** (C1'24) - [here:](https://docs.google.com/spreadsheets/d/1sSl2UqQXkM4IIBiJAMcqX2CDhLrlc6PWE0EOqO6_Y88/edit?usp=sharing)

- with 4h Dev tasks.

# Initial Communication

- Request coming in through Sales (new client) or CS (existing clients).
- CS conducts a **15-minute call** to explain the procedure.
- Prerequisite(s) for the call and the migration:
  - active subscription with SEOmonitor, 
  - the tool they're migrating from,
  - how many campaigns and keywords,
  - devices.

- CS sends a **follow-up email** summarizing the discussion and includes a recording of the call (for future reference).

> Clients may provide **CSVs directly** or **authorize API access.**
# Migration via CSV (directly by the CS team) 

1. **File checks**
  - The file names should include the **exact URL** and **location**.
  - Data contained: **keywords**, **ranks**, **dates**, and **groups** (also known as **tags** in other tools).
    - The frequency of the ranks (dates) does not impact the migration process overall.
    - But if less than daily (i.e. weekly or monthly), the historical Visibility will be affected.

  - Separate CSVs for desktop and mobile. 
    - If only one CSV is available, desktop ranks will be uploaded for mobile.


  - Check received CSVs for accuracy (multiple dates, wrong ranks, etc).
  - Curate CSVs, if necessary, to meet migration requirements; for example, add a delimiter if there are no templates, or clean up the rows, as we have a 10k row limit.
  - If the CSV is larger than 100 MB (for example, we know STAT has large CSVs) or there are several CSVs for the same campaign, upload them as a zip archive.

1. **Migration**
  - Access the **owner**'s account, with _impersonate_ from [SMadmin](https://admin.seomonitor.com/users).
  - Go to [Campaign Settings](https://app.seomonitor.com/v2/account/company/campaign) and add `/migrations` at the end of the URL, like this: [https://app.seomonitor.com/v2/account/company/migrations.](https://app.seomonitor.com/v2/account/company/migrations)
  - Click on `Import Campaign`.
  - Select the corresponding template, or manually map the CSVs, if there's no template.
  - Upload each individual CSV.
  - Check the import and the campaign.
    - check if the ranks are imported altogether,
    - plus take some random keywords, if you suspect any issue.


1. Inform the client once done.
  1. if all files have been sent at once, inform them after it's fully done.
  1. if they send the files in batches, confirm per batch.


# Migration via API (CS team through Dev team)

> This is NOT preferable, as it can cost them extra, and other tools can have more limits via API.
- what tool do they need to extract from,
- credentials: username and password,
- number of domains and keywords,
- how much historical data,
- task in clickup for Devs.

---

**2021 update: obsolete as of the above 2024 ones**

**FOR INTERNAL PURPOSES ONLY:**

STEPS TO FOLLOW:


1. Add the user's email address and name from [here](https://monosnap.com/file/i523yzAEbSJfljDT6VafNulsb6C8lm).                                                                                                                                                                                                        Ask the user to fill in the first two columns from the blueprint by making sure to use the [provided URL](https://app.seomonitor.com/v2/migrations-location-tool) as shown [here](https://monosnap.com/file/jVteC8UlWrZMTnXZ6Lon9HDzNBDBK2).
1. After user has confirmed that he added all the campaign URLs and markets, sync data from [here](https://monosnap.com/file/Xl5wCKOyhhUmgZHvAMWrMb0akbS6SR).
1. Then go back to the user and ask him/her to upload the CSV documents with the keywords & ranks for [each of the devices](https://take.ms/iioyg). *NOTE: the CSVs they upload should contain only the necessary info: ranks, date, keywords and/or groups (bearing in mind that if a keyword should be present in more than 1 group, you can add all the names of the groups in the same cell separated by comma, slash or semicolon).
1. The next step is for the [blueprint to be populated](https://take.ms/wYuyW) both with the links to the files and the data found in those files (the yellow area).
1. After this, the client needs to check the accuracy of the data we found and validate it accordingly by double clicking in the cell and [selecting YES/NO](https://take.ms/3ldOP).
1. Following a positive validation, we need to click on "Import" [here](https://monosnap.com/file/mQyyzhyRvBVDdRA1td3haCvA1ejG1Z) and follow the steps from the tool. 
1. After importing the first campaign the rest of the campaigns will be done automatically, since this is basically the template for the migration. Once this is done, you'll see the [green area of the blueprint](https://take.ms/Q0ei7) being populated, these wili be the data we'll be showing in the app.
1. After this step, we'll need to check if there are any differences between the yellow area and the green one and [validate it.](https://take.ms/H3TVZ)
1. If this validation has been a positive one from the CS side, the client will also have to do a [final validation](https://take.ms/LCzDF).
1. The last step, after the client's validation, is [closing the migration from SEOadmin.](https://take.ms/SqM0yv)



**FOR CLIENT ONLY, TEMPLATE FOR THE FIRST EMAIL SENT**

This is the first step when doing a migration, here's a template to help you send the first email.

Getting back to you with the details regarding the migration process as promised:

- initially you will receive 2 emails from us that will give you access to a folder in drive, which is the actual interface from your end, for the migration of the campaigns (you can find the emails in your inbox already).
- the first step you need to do is to fill in the first two columns in the blueprint you see in that folder (in order to select the Google market, please use the [provided URL](https://app.seomonitor.com/v2/migrations-location-tool) and copy clipboard exactly as it is there).
- once you finished filling in the blueprint, please get back to me to confirm this, so I can update the info on our end.
- after I've updated it, you can go in the 'Import file' folder, where you can find new folders for each of the campaigns you added in the blueprint;
- you then go in turn, into each of the folders for the campaigns, and upload the CSV documents with the keywords & ranks for [each of the devices](https://take.ms/iioyg) that you've exported from the previous tool (STAT in this case). We recommend that the CSVs you upload, contain only the necessary info: ranks, date, keywords and/or groups (bear in mind that if a keyword should be present in more than 1 group, you can add all the names of the groups in the same cell (separated by comma, slash or semicolon).
- once you've uploaded all the CSVs, simply go back to the Blueprint and on the 'Client Validation' column select from the drop-down yes or no, as a final ok, before we migrate the provided data.
- after positively validating the migration of the campaigns in the blueprint, please let me know, so I can move the process in its final phase.
- after a couple of checks on my end, I will get back to you so you can also validate everything.

During this process you will be able to see and access these campaigns in your account, but please bear in mind that you shouldn't modify them until the process is finalized.
