#!/bin/bash
# Guru Card Daily Scan
# Runs the generator to find new threads, then updates the dashboard.
# Scheduled via cron to run daily at 9:00 AM.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$SCRIPT_DIR/guru_daily.log"
PYTHON="/usr/bin/env python3"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$LOG_FILE"
echo "🕐 $(date '+%Y-%m-%d %H:%M:%S') — Daily Guru scan starting" >> "$LOG_FILE"

# Step 1: Scan Slack for new threads (last 7 days)
cd "$SCRIPT_DIR"
$PYTHON guru_card_generator.py --days 7 >> "$LOG_FILE" 2>&1

# Step 2: Update dashboard and push to Netlify
$PYTHON update_dashboard.py --push >> "$LOG_FILE" 2>&1

echo "✅ $(date '+%Y-%m-%d %H:%M:%S') — Done" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
