#!/usr/bin/env python3
"""
ClickUp Comment Monitor - Using Antigravity's MCP Tools
Monitors open ClickUp tasks for new comments and sends Slack alerts.

This script is designed to be called by Antigravity's task system.
It expects to be run with access to MCP ClickUp tools.
"""

import os
import json
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
STATE_FILE = os.path.join(os.path.dirname(__file__), "clickup_comment_state.json")

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

def filter_open_tasks(tasks_data):
    """Filter to only open tasks (exclude closed/completed)."""
    closed_statuses = ['closed', 'completed', 'archived']
    
    # Handle different response formats
    if isinstance(tasks_data, dict):
        tasks = tasks_data.get('results', [])
    elif isinstance(tasks_data, str):
        # Parse JSON string if needed
        tasks_data = json.loads(tasks_data)
        tasks = tasks_data.get('results', [])
    else:
        tasks = tasks_data
    
    return [t for t in tasks if t.get('status', '').lower() not in closed_statuses and not t.get('archived', False)]

def is_comment_from_today(comment_timestamp_ms):
    """Check if comment was posted in the last 24 hours."""
    try:
        comment_time = datetime.fromtimestamp(int(comment_timestamp_ms) / 1000, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - comment_time) < timedelta(hours=24)
    except (ValueError, TypeError) as e:
        print(f"      ⚠️  Error parsing timestamp {comment_timestamp_ms}: {e}")
        return False

def send_slack_alert(task, comment, webhook_url):
    """Send Slack notification about new comment."""
    # Extract comment text
    comment_text = comment.get('comment_text', '')
    if len(comment_text) > 200:
        comment_text = comment_text[:200] + "..."
    
    user = comment.get('user', {})
    username = user.get('username', 'Unknown')
    
    # Format timestamp
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
                    {"title": "Task", "value": f"<{task['url']}|{task['name'][:100]}>", "short": False},
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
            print(f"      ✅ Slack alert sent")
            return True
        else:
            print(f"      ❌ Failed to send Slack alert: {resp.status_code}")
            return False
    except Exception as e:
        print(f"      ❌ Error sending Slack alert: {e}")
        return False

def process_tasks_and_comments(tasks_json, comments_by_task, webhook_url, dry_run=False):
    """
    Process tasks and their comments to find new comments from today.
    
    Args:
        tasks_json: JSON string or dict with ClickUp search results
        comments_by_task: Dict mapping task_id to comments JSON/dict
        webhook_url: Slack webhook URL
        dry_run: If True, only print what would be sent
    
    Returns:
        Number of alerts sent
    """
    # Parse tasks if needed
    if isinstance(tasks_json, str):
        tasks_data = json.loads(tasks_json)
    else:
        tasks_data = tasks_json
    
    # Load state
    state = load_state()
    seen_comments = state.get("seen_comments", {})
    new_alerts = 0
    
    # Filter for open tasks
    open_tasks = filter_open_tasks(tasks_data)
    print(f"📋 Found {len(open_tasks)} open tasks")
    
    # Process each open task
    for task in open_tasks:
        task_id = task['id']
        task_name = task.get('name', 'Unknown')[:50]
        
        # Get comments for this task
        if task_id not in comments_by_task:
            continue
        
        comments_data = comments_by_task[task_id]
        
        # Parse comments if needed
        if isinstance(comments_data, str):
            comments_data = json.loads(comments_data)
        
        comments = comments_data.get('comments', [])
        if not comments:
            continue
        
        print(f"\n   Task {task_id}: {task_name}")
        print(f"   Found {len(comments)} comment(s)")
        
        # Check for new comments from today
        for comment in comments:
            comment_id = comment['id']
            comment_date = comment['date']
            
            # Skip if we've already seen this comment
            if task_id in seen_comments and comment_id in seen_comments.get(task_id, []):
                continue
            
            # Skip if comment is not from today
            if not is_comment_from_today(comment_date):
                continue
            
            # New comment from today!
            user = comment.get('user', {}).get('username', 'Unknown')
            print(f"   🆕 New comment from {user}")
            
            if dry_run:
                print(f"   [DRY RUN] Would send alert to Slack")
                new_alerts += 1
            else:
                # Send alert
                if send_slack_alert(task, comment, webhook_url):
                    # Mark as seen
                    if task_id not in seen_comments:
                        seen_comments[task_id] = []
                    seen_comments[task_id].append(comment_id)
                    new_alerts += 1
    
    # Update state
    state['seen_comments'] = seen_comments
    state['last_check'] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    
    print(f"\n✅ Scan complete: {new_alerts} new alert(s) {'would be sent' if dry_run else 'sent'}")
    print(f"📝 State saved to {STATE_FILE}")
    
    return new_alerts

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor ClickUp tasks for new comments")
    parser.add_argument("--dry-run", action="store_true", help="Test mode - don't send Slack alerts")
    parser.add_argument("--tasks-file", type=str, help="Path to JSON file with tasks data")
    parser.add_argument("--comments-dir", type=str, help="Directory with comment JSON files")
    args = parser.parse_args()
    
    print("⚠️  This script should be called by Antigravity with MCP data")
    print("   For standalone testing, provide --tasks-file and --comments-dir")
    
    if args.tasks_file and args.comments_dir:
        # Load test data
        with open(args.tasks_file) as f:
            tasks_json = f.read()
        
        # Load comments
        comments_by_task = {}
        import glob
        for comments_file in glob.glob(f"{args.comments_dir}/*.json"):
            task_id = os.path.basename(comments_file).replace('.json', '')
            with open(comments_file) as f:
                comments_by_task[task_id] = f.read()
        
        process_tasks_and_comments(
            tasks_json, 
            comments_by_task, 
            SLACK_WEBHOOK_URL, 
            dry_run=args.dry_run
        )
    else:
        print("\n❌ Missing required arguments for standalone mode")
        print("   Use --tasks-file and --comments-dir")
