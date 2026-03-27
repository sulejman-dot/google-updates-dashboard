# How to Add the `/clickup` Slash Command to Your Slack App

This guide will help you create a `/clickup` slash command in your Slack App that connects to your local bot server.

## Prerequisites

- You need a Slack App already created (if not, follow the basic app creation steps from `slack_setup_guide.md`)
- Your bot server should be running on `http://localhost:3000`
- You need ngrok or a similar tunneling service to expose your local server to the internet

## Step 1: Start Your Local Server & Tunnel

### 1.1 Start the Slack Bot Server

```bash
cd "/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Sulejman Workspace"
python3 slack_bot_server.py
```

You should see: `🚀 Server starting on http://localhost:3000`

### 1.2 Start ngrok Tunnel

In a **new terminal window**, run:

```bash
ngrok http 3000
```

You'll see output like:
```
Forwarding    https://abc123.ngrok.io -> http://localhost:3000
```

**Copy the `https://` URL** - you'll need it in the next steps.

> [!IMPORTANT]
> Keep both the server and ngrok running throughout this setup process.

## Step 2: Configure Slash Command in Slack App

### 2.1 Go to Your Slack App Settings

1. Visit [api.slack.com/apps](https://api.slack.com/apps)
2. Click on your app (e.g., "ClickUp Guardian" or whatever you named it)

### 2.2 Create the Slash Command

1. In the left sidebar, under **Features**, click **Slash Commands**
2. Click **Create New Command**
3. Fill in the form:

   | Field | Value |
   |-------|-------|
   | **Command** | `/clickup` |
   | **Request URL** | `https://YOUR-NGROK-URL/slack/command` |
   | **Short Description** | `View your open ClickUp tasks` |
   | **Usage Hint** | _(leave empty or add: "Shows tasks assigned to you")_ |

4. Click **Save**

### 2.3 Example Request URL

If your ngrok URL is `https://abc123.ngrok.io`, your Request URL should be:
```
https://abc123.ngrok.io/slack/command
```

## Step 3: Reinstall Your App (Required!)

> [!WARNING]
> After adding a new slash command, you **must** reinstall the app to your workspace.

1. In the left sidebar, click **Install App**
2. Click **Reinstall to Workspace**
3. Review the permissions and click **Allow**

## Step 4: Test the Command

1. Go to any Slack channel in your workspace
2. Type `/clickup` and press Enter
3. You should see your 9 open ClickUp tasks displayed with:
   - Task names (clickable links)
   - Custom IDs (e.g., PRODUCT-4859)
   - Status
   - Tags
   - Assignees
   - Color coding (red for bugs, green for features, orange for others)

## Troubleshooting

### Command Not Found
- **Issue:** Slack says "Command not found"
- **Fix:** Make sure you reinstalled the app after creating the command

### Dispatch Failed
- **Issue:** Slack shows "dispatch_failed" error
- **Fix:** 
  1. Check that ngrok is running
  2. Verify the Request URL in Slack App settings matches your ngrok URL
  3. Make sure your bot server is running on port 3000

### No Response
- **Issue:** Command runs but no response appears
- **Fix:**
  1. Check the bot server terminal for errors
  2. Verify the `/slack/command` endpoint is working by visiting `https://YOUR-NGROK-URL/` (should show "✅ Bot Server is Running!")

### ngrok URL Changes
- **Issue:** ngrok URL changes every time you restart it
- **Fix:** 
  1. Get a permanent ngrok domain (requires ngrok account)
  2. Or update the Request URL in Slack App settings each time ngrok restarts

## Keeping It Running

### Option 1: Use the Keep Alive Script

```bash
./keep_bot_alive.sh
```

This will automatically restart the bot if it crashes.

### Option 2: Use a Permanent Tunnel

For a production setup, consider:
- ngrok paid plan with a static domain
- Deploy to a cloud server (Heroku, AWS, etc.)
- Use a reverse proxy service

## Additional Commands Available

Your bot also supports these commands (add them the same way):

| Command | Description |
|---------|-------------|
| `/hello` | Test command - bot says hello |
| `/check-invoices` | View overdue invoices |
| `/wbr` | Weekly business review summary |
| `/intercom` | Intercom inbox summary |
| `/intercom-report` | Intercom OKR report |
| `/intercom-audit` | CSAT audit report |
| `/test-api` | SEOmonitor API testing modal |

To add any of these, repeat Step 2 with the appropriate command name.

## Next Steps

Once the `/clickup` command is working:
1. ✅ Test it regularly to ensure your tasks are up to date
2. 📝 Consider adding the other commands for a complete bot experience
3. 🔄 Set up automatic updates to `fetch_clickup_tasks.py` to keep task data fresh

---

> [!TIP]
> **Pro Tip:** Create a dedicated Slack channel like `#bot-commands` to test your commands without cluttering other channels.
