# 🔧 Google Service Account Setup - Step-by-Step Guide

Follow these steps to connect your `/wbr` Slack command to your Google Sheet.

## ✅ Step 1: Create Google Cloud Project

1. **Open**: https://console.cloud.google.com/
2. **Click**: "Select a project" dropdown (top bar)
3. **Click**: "NEW PROJECT"
4. **Enter name**: `Slack Bot WBR` (or any name you prefer)
5. **Click**: "CREATE"
6. **Wait** for the project to be created (~10 seconds)

---

## ✅ Step 2: Enable Google Sheets API

1. **Make sure** your new project is selected (check top bar)
2. **Click**: ☰ Menu → "APIs & Services" → "Library"
3. **Search**: "Google Sheets API"
4. **Click** on "Google Sheets API"
5. **Click**: "ENABLE"
6. **Go back** to Library
7. **Search**: "Google Drive API"
8. **Click** on "Google Drive API"
9. **Click**: "ENABLE"

---

## ✅ Step 3: Create Service Account

1. **Click**: ☰ Menu → "APIs & Services" → "Credentials"
2. **Click**: "+ CREATE CREDENTIALS" (top)
3. **Select**: "Service Account"
4. **Fill in**:
   - Service account name: `slack-bot-reader`
   - Service account ID: (auto-filled, leave as is)
   - Description: "Reads WBR Google Sheet for Slack bot"
5. **Click**: "CREATE AND CONTINUE"
6. **For Role**: Select "Viewer" (under "Basic" roles)
7. **Click**: "CONTINUE"
8. **Click**: "DONE"

---

## ✅ Step 4: Download JSON Key

1. You should now see your service account in the list
2. **Click** on the service account email (`slack-bot-reader@...`)
3. **Go to** the "KEYS" tab
4. **Click**: "ADD KEY" → "Create new key"
5. **Select**: JSON
6. **Click**: "CREATE"
7. **A file downloads** (e.g., `slack-bot-wbr-xxxxx.json`)
8. **SAVE THIS FILE** - we'll need it in the next step!

---

## ✅ Step 5: Share Your Google Sheet

1. **Open** the downloaded JSON file in a text editor
2. **Find** the `"client_email"` line (looks like: `"slack-bot-reader@project-12345.iam.gserviceaccount.com"`)
3. **Copy** that email address (just the email, no quotes)
4. **Open** your WBR Google Sheet: https://docs.google.com/spreadsheets/d/161qbyJ5nQsgDEaudZ5O1C4zldUIBbeDiYMYyCgldG40
5. **Click**: "Share" button (top right)
6. **Paste** the service account email
7. **Permission**: Make sure it's set to "Viewer"
8. **Uncheck** "Notify people" (it's a robot, no need)
9. **Click**: "Share" or "Send"

---

## ✅ Step 6: Upload JSON File to Workspace

**Now I need you to:**

1. Locate the JSON file you downloaded (e.g., `slack-bot-wbr-xxxxx.json`)
2. **Tell me the path** to that file, and I'll move it to the correct location

**Or:**

Simply **paste the entire contents** of the JSON file here, and I'll create the `service_account.json` file for you.

---

## 🎯 After Setup Complete:

Once the JSON file is in place:
- ✅ `/wbr` command will use **real data** from your Google Sheet
- ✅ Reads automatically from the first worksheet
- ✅ Shows the value from cell A1 as the key metric

**What data should the WBR sheet contain?** Let me know and I can customize what it reads!
