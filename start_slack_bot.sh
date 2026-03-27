#!/bin/bash
# =============================================================
# Slack Bot Auto-Start Script (Idempotent)
# Starts the Slack bot server + ngrok if not already running
# Also runs a catch-up comment check after first startup
# =============================================================

WORKSPACE_DIR="/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Sulejman Workspace"
LOG_FILE="$WORKSPACE_DIR/startup.log"
NGROK_DOMAIN="prevertebral-preadequately-lezlie.ngrok-free.dev"
STARTED_SOMETHING=false

cd "$WORKSPACE_DIR"

# --- 1. Check and start ngrok if needed ---
if ! pgrep -f "ngrok http" > /dev/null 2>&1; then
    echo "[$(date)] Starting ngrok tunnel on domain $NGROK_DOMAIN..." >> "$LOG_FILE"
    /opt/homebrew/bin/ngrok http 3000 --domain="$NGROK_DOMAIN" >> /dev/null 2>&1 &
    echo "[$(date)] ngrok started (PID: $!)" >> "$LOG_FILE"
    STARTED_SOMETHING=true
    sleep 3
else
    echo "[$(date)] ngrok already running, skipping." >> "$LOG_FILE"
fi

# --- 2. Check and start Slack bot if needed ---
if ! pgrep -f "slack_bot_server.py" > /dev/null 2>&1; then
    echo "[$(date)] Starting Slack bot server..." >> "$LOG_FILE"
    /usr/bin/python3 "$WORKSPACE_DIR/slack_bot_server.py" >> "$WORKSPACE_DIR/slack_bot.log" 2>&1 &
    echo "[$(date)] Slack bot started (PID: $!)" >> "$LOG_FILE"
    STARTED_SOMETHING=true
    sleep 5
else
    echo "[$(date)] Slack bot already running, skipping." >> "$LOG_FILE"
fi

# --- 3. Catch-up comment check (only on fresh start) ---
if [ "$STARTED_SOMETHING" = true ]; then
    echo "[$(date)] Running catch-up comment check after startup..." >> "$LOG_FILE"
    curl -s -X POST "http://localhost:3000/slack/command" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "command=/clickup-comments&user_id=AUTO&user_name=startup-catchup&channel_id=AUTO&response_url=none" \
      >> "$LOG_FILE" 2>&1
    echo "" >> "$LOG_FILE"
    echo "[$(date)] ✅ Catch-up check complete." >> "$LOG_FILE"
fi
