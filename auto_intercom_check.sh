#!/bin/bash
# Auto Intercom Response Check - Direct Agent Invocation
# Runs every 5 minutes via cron to check for slow Intercom responses

WORKSPACE_DIR="/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Sulejman Workspace"
LOG_FILE="$WORKSPACE_DIR/intercom_monitor.log"

cd "$WORKSPACE_DIR"

echo "========================================" >> "$LOG_FILE"
echo "Auto Intercom Check: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Run the auto monitor script which calls the Slack bot endpoint
python3 "$WORKSPACE_DIR/auto_intercom_monitor.py" >> "$LOG_FILE" 2>&1

echo "Check completed at $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
