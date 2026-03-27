# Interactive Bot Setup Guide

To make your bot respond to commands (like `/hello`), we need to connect "Slack" to your "Local Computer" via a tunnel.

## Step 1: Start the Local Server
1. Open a terminal in your workspace.
2. Run the server script:
   ```bash
   python3 slack_bot_server.py
   ```
   *You should see: `Running on http://127.0.0.1:3000`*

## Step 2: Start ngrok Tunnel
1. Open a **new** terminal window (keep the server running).
2. If you haven't authenticated ngrok yet:
   - Go to [dashboard.ngrok.com](https://dashboard.ngrok.com) -> Sign Up/Login.
   - Copy your **Authtoken**.
   - Run: `ngrok config add-authtoken YOUR_TOKEN`
3. Start the tunnel:
   ```bash
   ngrok http 3000
   ```
4. Copy the **Forwarding URL** (e.g., `https://a1b2-c3d4.ngrok-free.app`).

## Step 3: Configure Slack App
1. Go back to your [Slack App Settings](https://api.slack.com/apps).
2. Select your App ("ClickUp Guardian").
3. In the sidebar, click **Slash Commands** -> **Create New Command**.
4. **Command:** `/hello`
5. **Request URL:** Paste your ngrok URL + `/slack/command`
   - Example: `https://a1b2-c3d4.ngrok-free.app/slack/command`
6. **Short Description:** "Say hello"
7. Click **Save**.

## Step 4: Test It!
1. Go to Slack.
2. Type `/hello`.
3. Your bot should reply!

---
> [!NOTE]
> If you close the terminal running `ngrok`, the URL will stop working. You'll need to restart ngrok and update the URL in Slack (unless you have a paid ngrok account).
