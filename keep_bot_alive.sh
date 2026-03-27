#!/bin/bash

# Configuration
BOT_SCRIPT="slack_bot_server.py"
NGROK_URL="prevertebral-preadequately-lezlie.ngrok-free.dev"
PORT=3000
LOG_FILE="bot_stability.log"
PYTHON_BIN="/usr/bin/python3"
WORKSPACE_DIR="/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Sulejman Workspace"

cd "$WORKSPACE_DIR"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 1. Check Slack Bot Server
if ! ps aux | grep "$BOT_SCRIPT" | grep -v grep > /dev/null; then
    log_message "⚠️ Slack Bot Server is down. Restarting..."
    nohup "$PYTHON_BIN" "$BOT_SCRIPT" >> "$LOG_FILE" 2>&1 &
    log_message "✅ Slack Bot Server restarted."
else
    log_message "ℹ️ Slack Bot Server is running."
fi

# 2. Check ngrok Tunnel
if ! ps aux | grep "ngrok" | grep "$NGROK_URL" | grep -v grep > /dev/null; then
    log_message "⚠️ ngrok tunnel is down. Restarting..."
    nohup ngrok http --url="$NGROK_URL" "$PORT" >> "$LOG_FILE" 2>&1 &
    log_message "✅ ngrok tunnel restarted."
else
    log_message "ℹ️ ngrok tunnel is running."
fi
