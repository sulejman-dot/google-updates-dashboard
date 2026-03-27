# Google Sheets API Setup Guide

Follow these steps to enable your Slack bot to read your WBR Google Sheet.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Name it: `Slack Bot WBR`
4. Click **"Create"**

## Step 2: Enable Google Sheets API

1. In your new project, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Sheets API"**
3. Click on it and press **"Enable"**
4. Also search for **"Google Drive API"** and enable it

## Step 3: Create Service Account

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"+ Create Credentials"** → **"Service Account"**
3. Fill in:
   - **Service account name**: `slack-bot-reader`
   - **Service account ID**: (auto-filled)
4. Click **"Create and Continue"**
5. For **"Role"**, select **"Viewer"** (read-only access)
6. Click **"Continue"** → **"Done"**

## Step 4: Generate JSON Key

1. In **"Credentials"**, find your new service account
2. Click on it to open details
3. Go to **"Keys"** tab
4. Click **"Add Key"** → **"Create new key"**
5. Choose **"JSON"** format
6. Click **"Create"**
7. A JSON file will download automatically (e.g., `slack-bot-wbr-xxxxx.json`)

## Step 5: Share Your Google Sheet

1. Open the downloaded JSON file
2. Find the `"client_email"` field (looks like: `slack-bot-reader@project-id.iam.gserviceaccount.com`)
3. **Copy this email address**
4. Open your WBR Google Sheet
5. Click **"Share"** button
6. Paste the service account email
7. Set permission to **"Viewer"**
8. Click **"Send"**

## Step 6: Save Credentials to Workspace

**Paste the JSON file path here, and I'll move it to the right location.**

The file should be named `google_credentials.json` and placed in your workspace folder.

---

**Once you complete these steps, let me know and I'll update the bot to use real data!**
