#!/bin/bash
# Auto ClickUp Comment Check - Triggers via Slack Bot Endpoint
# Runs every 5 minutes via cron to check for new ClickUp comments

WORKSPACE_DIR="/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Sulejman Workspace"
LOG_FILE="$WORKSPACE_DIR/comment_monitor.log"

cd "$WORKSPACE_DIR"

echo "========================================" >> "$LOG_FILE"
echo "Auto Comment Check: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Trigger the /clickup-comments command via curl to localhost
# This uses the same handler as the Slack command but triggered locally
curl -s -X POST "http://localhost:3000/slack/command" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "command=/clickup-comments&user_id=AUTO&user_name=cron&channel_id=AUTO&response_url=none" \
  >> "$LOG_FILE" 2>&1

echo "Check completed at $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
