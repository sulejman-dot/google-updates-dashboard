#!/bin/bash
# ClickUp Comment Monitor - Cron Runner
# This script triggers a comment check by calling the Gemini agent

WORKSPACE_DIR="/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Sulejman Workspace"
LOG_FILE="$WORKSPACE_DIR/comment_monitor.log"

cd "$WORKSPACE_DIR"

echo "========================================" >> "$LOG_FILE"
echo "ClickUp Comment Check: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Run the Python script that uses MCP integration
python3 "$WORKSPACE_DIR/clickup_comment_check.py" >> "$LOG_FILE" 2>&1

echo "" >> "$LOG_FILE"
