#!/bin/bash
# Wrapper script to run Google Update Monitor
WORKSPACE_DIR="/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Sulejman Workspace"

cd "$WORKSPACE_DIR"
/usr/bin/python3 google_update_monitor.py >> google_monitor.log 2>&1
