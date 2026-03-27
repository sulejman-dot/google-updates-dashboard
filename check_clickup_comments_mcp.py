#!/usr/bin/env python3
"""
ClickUp Comment Monitor using MCP Tools
Checks for new comments on open tasks and sends Slack alerts
"""

import os
import json
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

STATE_FILE = os.path.join(os.path.dirname(__file__), "clickup_comment_state.json")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def load_state():
    """Load the last check timestamp and seen comment IDs."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_check": None, "seen_comments": {}}

def save_state(state):
    """Save the current state to file."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def is_comment_from_last_24h(comment_timestamp_ms):
    """Check if comment was posted in the last 24 hours."""
    try:
        comment_time = datetime.fromtimestamp(int(comment_timestamp_ms) / 1000, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - comment_time) < timedelta(hours=24)
    except (ValueError, TypeError) as e:
        print(f"⚠️  Error parsing timestamp {comment_timestamp_ms}: {e}")
        return False

def send_slack_alert(task_name, task_url, comment, webhook_url):
    """Send Slack notification about new comment."""
    comment_text = comment.get('comment_text', '')
    if len(comment_text) > 200:
        comment_text = comment_text[:200] + "..."
    
    user = comment.get('user', {})
    username = user.get('username', 'Unknown')
    
    try:
        comment_time = datetime.fromtimestamp(int(comment['date']) / 1000)
        time_str = comment_time.strftime("%b %d at %H:%M UTC")
    except:
        time_str = "Unknown time"
    
    msg = {
        "text": f"💬 *New ClickUp Comment*",
        "username": "ClickUp Monitor",
        "icon_emoji": ":speech_balloon:",
        "attachments": [
            {
                "color": "#7B68EE",
                "fields": [
                    {"title": "Task", "value": f"<{task_url}|{task_name[:100]}>", "short": False},
                    {"title": "From", "value": username, "short": True},
                    {"title": "When", "value": time_str, "short": True},
                    {"title": "Comment", "value": comment_text, "short": False}
                ]
            }
        ]
    }
    
    try:
        resp = requests.post(webhook_url, json=msg)
        if resp.status_code == 200:
            print(f"   ✅ Slack alert sent for task: {task_name[:50]}")
            return True
        else:
            print(f"   ❌ Failed to send Slack alert: {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error sending Slack alert: {e}")
        return False

def main():
    print("🔎 ClickUp Comment Monitor (MCP)")
    
    if not SLACK_WEBHOOK_URL:
        print("❌ SLACK_WEBHOOK_URL not found in environment")
        return 1
    
    # Load state
    state = load_state()
    seen_comments = state.get("seen_comments", {})
    new_alerts = 0
    
    # Import MCP tools
    try:
        # Add parent directory to path to import MCP tools
        import sys
        sys.path.insert(0, os.path.dirname(__file__))
        
        # For now, we'll use the Python subprocess approach to call MCP tools
        # This is a simplified version - in production, Antigravity would handle this
        print("\n📡 Note: This script requires MCP ClickUp integration")
        print("   Running in standalone mode with limited functionality")
        print("   For full functionality, run via Antigravity workflow")
        
        # Placeholder - you would call MCP tools here
        print("\n✅ Monitor check complete (test mode)")
        print("ℹ️  To enable full monitoring, run: /clickup-comments workflow in Antigravity")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Save state
    state['last_check'] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
