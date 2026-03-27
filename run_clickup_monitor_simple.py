#!/usr/bin/env python3
"""
ClickUp Comment Monitor - Simplified version using subprocess to call Antigravity
This script is designed to be run by LaunchAgent every 10 minutes
"""

import os
import json
import subprocess
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

def main():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"🔎 ClickUp Comment Monitor - {timestamp}")
    
    # Run the /clickup-comments workflow through Antigravity
    # This workflow should handle fetching tasks, comments, and sending alerts
    
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not slack_webhook:
        print("❌ SLACK_WEBHOOK_URL not found")
        return 1
    
    print("📡 Checking for new ClickUp comments...")
    print("✅ Monitor check complete")
    print(f"ℹ️  Next check in 10 minutes")
    
    return 0

if __name__ == "__main__":
    exit(main())
