#!/usr/bin/env python3
"""
ClickUp Comment Alert - Send a test alert for Vlad's comment
This demonstrates the alert functionality working
"""

import os
import requests
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# The comment data from task 869c3mu4c
comment = {
    "id": "90120192257242",
    "comment_text": "One refused keywords (in the original crawl for this site) did not got a corresponding row in the new gpt_search.keywords_sites_flags table...",
    "user": {
        "id": 36492063,
        "username": "Vlad Dragu",
        "email": "vlad.d@seomonitor.com"
    },
    "date": "1770900124827"
}

task_name = "[bug][rt] AIS widget stuck with analyzing keywords"
task_url = "https://app.clickup.com/t/869c3mu4c"

# Format alert
comment_time = datetime.fromtimestamp(int(comment['date']) / 1000, tz=timezone.utc)
time_str = comment_time.strftime("%b %d at %H:%M UTC")

msg = {
    "text": f"💬 *New ClickUp Comment* (Test Alert)",
    "username": "ClickUp Monitor",
    "icon_emoji": ":speech_balloon:",
    "attachments": [
        {
            "color": "#7B68EE",
            "fields": [
                {"title": "Task", "value": f"<{task_url}|{task_name}>", "short": False},
                {"title": "From", "value": comment['user']['username'], "short": True},
                {"title": "When", "value": time_str, "short": True},
                {"title": "Comment", "value": comment['comment_text'][:200], "short": False}
            ]
        }
    ]
}

print("📤 Sending test alert to Slack...")
resp = requests.post(SLACK_WEBHOOK_URL, json=msg, timeout=10)

if resp.status_code == 200:
    print("✅ Test alert sent successfully!")
    print(f"\nThis is what the alert for Vlad's comment looks like.")
    print(f"Comment was posted: {time_str}")
else:
    print(f"❌ Failed: {resp.status_code}")
    print(resp.text)
