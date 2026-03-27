#!/usr/bin/env python3
"""
ClickUp Comment Monitor - Simplified Polling Version
Checks for new comments on your assigned tasks and sends Slack notifications.

This version is designed to be run manually or via cron.
For MCP integration, you'll need to call this through the Gemini API or similar.
"""

import os
import json
import time
import argparse
from datetime import datetime
from slack_sdk import WebClient
from dotenv import load_dotenv

load_dotenv()

# Configuration
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_ALERT_CHANNEL = os.getenv("SLACK_ALERT_CHANNEL", "@sulejman")
STATE_FILE = "comment_state.json"

slack_client = WebClient(token=SLACK_BOT_TOKEN)


def load_state():
    """Load the last-seen comment state from file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading state file: {e}")
            return {}
    return {}


def save_state(state):
    """Save the current state to file."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"❌ Error saving state: {e}")


def send_slack_notification(task_name, task_url, commenter_name, comment_text, comment_date):
    """Send a Slack notification for a new comment."""
    
    try:
        # Truncate long comments
        if len(comment_text) > 500:
            comment_text = comment_text[:500] + "... (truncated)"
        
        message = {
            "channel": SLACK_ALERT_CHANNEL,
            "text": f"🔔 New comment on: {task_name}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔔 New ClickUp Comment"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Task:*\n<{task_url}|{task_name}>"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*From:*\n{commenter_name}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Comment:*\n{comment_text}"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Posted at {comment_date}"
                        }
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Task"
                            },
                            "url": task_url,
                            "style": "primary"
                        }
                    ]
                }
            ]
        }
        
        slack_client.chat_postMessage(**message)
        print(f"✅ Sent notification for comment on: {task_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending Slack notification: {e}")
        return False


def check_task_comments(task_id, task_name, task_url, state):
    """
    Check a single task for new comments.
    
    NOTE: This function needs to be called with MCP data.
    To use this script, you need to:
    1. Get your tasks using ClickUp MCP search
    2. For each task, get comments using ClickUp MCP
    3. Pass the data to this function
    
    This is a helper function that processes the comment data.
    """
    # This is a placeholder - in actual use, you'd pass comments_data as a parameter
    # For now, return 0 to indicate no new comments found
    return 0


def main():
    parser = argparse.ArgumentParser(description="ClickUp Comment Monitor")
    parser.add_argument('--test', action='store_true', help='Send a test notification')
    
    args = parser.parse_args()
    
    if not SLACK_BOT_TOKEN:
        print("❌ Error: SLACK_BOT_TOKEN not found in .env file")
        return
    
    print("🚀 ClickUp Comment Monitor")
    print(f"   Notifications will be sent to: {SLACK_ALERT_CHANNEL}")
    
    if args.test:
        print("\n📤 Sending test notification...")
        send_slack_notification(
            task_name="Test Task",
            task_url="https://app.clickup.com/t/test",
            commenter_name="Test User",
            comment_text="This is a test comment to verify Slack notifications are working!",
            comment_date=datetime.now().strftime('%Y-%m-%d %H:%M')
        )
        print("✅ Test complete!")
        return
    
    print("\n" + "="*60)
    print("IMPORTANT: MCP Integration Required")
    print("="*60)
    print("""
This script requires integration with ClickUp MCP to function.

To use this monitor, you need to:

1. Call this script through the Gemini API with MCP access
2. Or integrate it into a system that has MCP access
3. Or manually provide task and comment data

For now, use the --test flag to verify Slack notifications work:
    python3 clickup_comment_monitor_simple.py --test

For a complete solution, please run this through the Gemini agent
which has access to ClickUp MCP tools.
    """)


if __name__ == "__main__":
    main()
