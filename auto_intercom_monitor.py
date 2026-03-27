#!/usr/bin/env python3
"""
Automated Intercom Response Monitor
Runs via cron to check for slow Intercom responses and alert in Slack.
Uses requests to call localhost Slack bot endpoint.
"""

import requests
import json
from datetime import datetime


def trigger_intercom_check():
    """Trigger Intercom monitoring via localhost Slack bot endpoint."""
    
    print(f"\n{'='*60}")
    print(f"Intercom Monitor Trigger: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        # Call the Slack bot's Intercom check endpoint
        url = "http://localhost:3000/slack/command"
        
        payload = {
            "command": "/intercom-alerts",
            "user_id": "AUTO",
            "user_name": "cron",
            "channel_id": "AUTO",
            "response_url": "none"
        }
        
        print(f"🔄 Sending request to {url}...")
        
        response = requests.post(
            url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ Intercom check triggered successfully")
            print(f"Response: {response.text[:200]}")
            return True
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Could not connect to Slack bot server at localhost:3000")
        print(f"   Make sure the Slack bot server is running!")
        return False
    except Exception as e:
        print(f"❌ Error triggering Intercom check: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    trigger_intercom_check()
