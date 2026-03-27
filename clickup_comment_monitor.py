#!/usr/bin/env python3
"""
ClickUp Comment Monitor - PRODUCTION VERSION
Integrated with Antigravity MCP tools
Run this from Antigravity to check for new comments on open tasks
"""

import os
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

STATE_FILE = os.path.join(os.path.dirname(__file__), "clickup_comment_state.json")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_check": None, "seen_comments": {}}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def send_slack_alert(task, comment, webhook_url):
    """Send Slack notification about new comment."""
    import requests
    
    comment_text = comment.get('comment_text', '')[:200]
    user = comment.get('user', {}).get('username', 'Unknown')
    
    try:
        comment_time = datetime.fromtimestamp(int(comment['date']) / 1000)
        time_str = comment_time.strftime("%b %d at %H:%M UTC")
    except:
        time_str = "Unknown time"
    
    msg = {
        "text": f"💬 *New ClickUp Comment*",
        "username": "ClickUp Monitor",
        "icon_emoji": ":speech_balloon:",
        "attachments": [{
            "color": "#7B68EE",
            "fields": [
                {"title": "Task", "value": f"<{task['url']}|{task['name'][:100]}>", "short": False},
                {"title": "From", "value": user, "short": True},
                {"title": "When", "value": time_str, "short": True},
                {"title": "Comment", "value": comment_text, "short": False}
            ]
        }]
    }
    
    resp = requests.post(webhook_url, json=msg)
    return resp.status_code == 200

# List of open task IDs to monitor (from earlier scan)
OPEN_TASK_IDS = [
    "869bwrnku",   # [bug][rt] AIO mentions metric is incorrect in competition
    "869c3mu4c",   # [bug][rt] AIS widget stuck with analyzing keywords
    "869c3ebv5",   # [bug][dashboard] Visibility discrepancy
    "869c3eftz",   # [improvement][looker] Competition Insights connector
    "869c3dy26",   # [bug][rt] Smart groups with AIS criteria showing 0 keywords
    "869c3dw22",   # [bug][research] SV for tracked kw in research
    "869c2tvk7",   # [bug][exports] Some of the competitors' ranks are empty
    "869c14cc2",   # [Bug][Rank Tracker] Client's website is not flagged for AIS mention
    "869c2p3ur",   # [bug][rt] AIS keywords stuck in processing
    "869c2yr03",   # [feature request][exports] Allow bulk export for sublocations
    "869btgtqc"    # Proactive Quality Assurance & CSAT Recovery
]

def check_task_comments(task_id, task_data, comments_data, state, webhook_url, dry_run=False):
    """Check for new comments on a specific task."""
    seen_comments = state.get("seen_comments", {})
    alerts_sent = 0
    
    comments = comments_data.get('comments', [])
    if not comments:
        return 0
    
    for comment in comments:
        comment_id = comment['id']
        comment_date = int(comment['date'])
        
        # Skip if already seen
        if task_id in seen_comments and comment_id in seen_comments.get(task_id, []):
            continue
        
        # Check if from last 24 hours
        comment_time = datetime.fromtimestamp(comment_date / 1000, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        if (now - comment_time) >= timedelta(hours=24):
            continue
        
        # New comment from today!
        user = comment.get('user', {}).get('username', 'Unknown')
        print(f"   🆕 New comment from {user} on {task_id}")
        
        if dry_run:
            print(f"   [DRY RUN] Would send alert to Slack")
        else:
            if send_slack_alert(task_data, comment, webhook_url):
                print(f"   ✅ Alert sent to Slack")
            else:
                print(f"   ❌ Failed to send alert")
        
        # Mark as seen
        if task_id not in seen_comments:
            seen_comments[task_id] = []
        seen_comments[task_id].append(comment_id)
        alerts_sent += 1
    
    return alerts_sent

# This function is called by Antigravity with MCP data
def run_check_with_mcp_data(tasks_search_result, comments_by_task_id, dry_run=False):
    """
    Main function to be called with MCP data.
    
    Args:
        tasks_search_result: Result from mcp_clickup_clickup_search
        comments_by_task_id: Dict of {task_id: result from mcp_clickup_clickup_get_task_comments}
        dry_run: If True, don't send Slack alerts
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url and not dry_run:
        print("❌ No SLACK_WEBHOOK_URL configured")
        return 0
    
    state = load_state()
    total_alerts = 0
    
    # Parse tasks
    if isinstance(tasks_search_result, str):
        tasks_data = json.loads(tasks_search_result)
    else:
        tasks_data = tasks_search_result
    
    # Build task lookup
    task_by_id = {}
    for task in tasks_data.get('results', []):
        task_by_id[task['id']] = task
    
    # Check comments for each task
    for task_id, comments_data in comments_by_task_id.items():
        if task_id not in task_by_id:
            continue
        
        task_data = task_by_id[task_id]
        alerts = check_task_comments(task_id, task_data, comments_data, state, webhook_url, dry_run)
        total_alerts += alerts
    
    # Save state
    save_state(state)
    print(f"\n✅ Complete: {total_alerts} alert(s) {'would be sent' if dry_run else 'sent'}")
    
    return total_alerts

if __name__ == "__main__":
    print("⚠️  This script should be called from Antigravity with MCP data")
    print("   See the Slack command `/clickup-comments` for automated use")
