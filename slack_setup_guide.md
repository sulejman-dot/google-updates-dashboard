# How to Set Up a Slack App for Alerts

Follow these steps to generate a Webhook URL for your `clickup_slack_alert.py` script.

## Step 1: Create the App
    1. Go to [api.slack.com/apps](https://api.slack.com/apps?new_app=1).
2. Click **Create New App**.
3. Select **"From scratch"**.
4. **App Name:** `ClickUp Alerter` (or similar).
5. **Pick a workspace:** Select the workspace where you want to post alerts.
6. Click **Create App**.

## Step 2: Enable Webhooks
1. In the left sidebar, under **Features**, select **Incoming Webhooks**.
2. Toggle the switch to **On**.

## Step 3: Create the Webhook
1. Scroll down to the bottom of the page.
2. Click **Add New Webhook to Workspace**.
3. Slack will ask for permission. Select the **Channel** where you want the bot to post (e.g., `#bot-testing` or create a private channel for yourself).
4. Click **Allow**.

## Step 4: Copy the URL
1. You will be redirected back to the app settings.
2. You should now see a **Webhook URL** in the table (starts with `https://hooks.slack.com/services/...`).
3. **Copy** this URL.

## Step 5: Test It
Run the script with your new URL:
```bash
python3 clickup_slack_alert.py --webhook "PASTE_YOUR_URL_HERE"
```

---
> [!TIP]
> Once confirmed working, you can save this URL to your `.env` file as `SLACK_WEBHOOK_URL` so you don't have to paste it every time.
