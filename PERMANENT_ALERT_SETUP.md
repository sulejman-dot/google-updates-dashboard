# 🚀 Permanent Alert System - Setup Complete

## Overview

Your Slack bot automation is now permanently configured with auto-start on boot and automated monitoring for both ClickUp and Intercom.

## ✅ What's Running

### Auto-Start Services (LaunchAgents)
Both services start automatically when your Mac boots and restart if they crash:

1. **Slack Bot Server** (`com.slackbot.server`)
   - Runs on http://localhost:3000
   - Handles all Slack commands
   - Logs: `slack_bot.log` and `slack_bot_error.log`

2. **ngrok Tunnel** (`com.ngrok.tunnel`)
   - Exposes localhost:3000 to the internet
   - Generates a new public URL on each restart
   - Logs: `ngrok.log` and `ngrok_error.log`

### Automated Monitoring (Cron Jobs)
Both run every 5 minutes:

1. **ClickUp Comment Monitor** (`auto_comment_check.sh`)
   - Checks for new comments on open tasks
   - Sends alerts to #cx-team-chat
   - Log: `comment_monitor.log`

2. **Intercom Response Monitor** (`auto_intercom_check.sh`)
   - Checks for conversations waiting 15+ minutes
   - Sends alerts to #cx-team-chat
   - Log: `intercom_monitor.log`

## 🔧 Management Commands

### Check LaunchAgent Status
```bash
launchctl list | grep -E '(slackbot|ngrok)'
```

### Manually Stop Services
```bash
launchctl unload ~/Library/LaunchAgents/com.slackbot.server.plist
launchctl unload ~/Library/LaunchAgents/com.ngrok.tunnel.plist
```

### Manually Start Services
```bash
launchctl load ~/Library/LaunchAgents/com.slackbot.server.plist
launchctl load ~/Library/LaunchAgents/com.ngrok.tunnel.plist
```

### View logs
```bash
tail -f slack_bot.log
tail -f ngrok.log
tail -f comment_monitor.log
tail -f intercom_monitor.log
```

### Check Cron Jobs
```bash
crontab -l
```

## 📋 Daily Restart Procedure

When you restart your Mac or want to restart the services:

1. **Services auto-start** (no action needed)
   - Slack bot and ngrok will start automatically

2. **Get new ngrok URL**
   ```bash
   curl -s http://127.0.0.1:4040/api/tunnels | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['tunnels'][0]['public_url'])"
   ```

3. **Update Slack App Config**
   - Go to https://api.slack.com/apps
   - Update "Slash Commands" URLs with new ngrok URL
   - Update "Interactivity & Shortcuts" URL with new ngrok URL

4. **Verify everything works**
   - Test `/hello` command in Slack
   - Check logs to confirm monitoring is running

## 🎯 Slack Commands Available

- `/hello` - Test bot connection
- `/clickup-comments` - Manual check for new comments
- `/intercom-alerts` - Manual check for slow responses
- `/analyze-competitor <url>` - Analyze competitor content
- `/check-tasks` - View your ClickUp tasks
- `/intercom` - View Intercom summary

## ⚙️ Files Created

**LaunchAgents:**
- `com.slackbot.server.plist` - Slack bot auto-start config
- `com.ngrok.tunnel.plist` - ngrok auto-start config
- `install_launchagents.sh` - Installation script

**Monitoring Scripts:**
- `auto_intercom_monitor.py` - Intercom monitoring logic
- `auto_intercom_check.sh` - Intercom cron wrapper
- `auto_comment_check.sh` - ClickUp cron wrapper

**Core Services:**
- `slack_bot_server.py` - Main Slack bot server
- `clickup_comment_monitor_mcp.py` - ClickUp comment logic
- `intercom_response_monitor.py` - Intercom response logic

## 🔄 Re-installing LaunchAgents

If you ever need to reinstall:
```bash
./install_launchagents.sh
```

## ✅ System Status

- ✅ Slack Bot Server: Running on localhost:3000
- ✅ ngrok Tunnel: Active and forwarding
- ✅ ClickUp Alerts: Automated every 5 minutes
- ✅ Intercom Alerts: Automated every 5 minutes
- ✅ Auto-start on boot: Enabled
- ✅ Auto-restart on crash: Enabled

---

**Last Updated:** 2026-02-12  
**Status:** Production Ready
