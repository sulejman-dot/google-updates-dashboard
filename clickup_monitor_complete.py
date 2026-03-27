#!/usr/bin/env python3
"""
ClickUp Comment Monitor - Uses ClickUp API directly
Checks for new comments on assigned tasks and sends Slack alerts

This script is designed to be run every 10 minutes by LaunchAgent.
"""

import os
import json
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

STATE_FILE = os.path.join(os.path.dirname(__file__), "clickup_comment_state.json")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
CLICKUP_API_KEY = os.getenv("CLICKUP_API_KEY")
BASE_URL = "https://api.clickup.com/api/v2"

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
        comment_time = datetime.fromtimestamp(int(comment['date']) / 1000, tz=timezone.utc)
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
        resp = requests.post(webhook_url, json=msg, timeout=10)
        if resp.status_code == 200:
            print(f"   ✅ Slack alert sent for task: {task_name[:50]}")
            return True
        else:
            print(f"   ❌ Failed to send Slack alert: {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error sending Slack alert: {e}")
        return False

def get_my_user_id():
    """Get the authenticated user's ID."""
    headers = {"Authorization": CLICKUP_API_KEY}
    try:
        resp = requests.get(f"{BASE_URL}/user", headers=headers, timeout=10)
        if resp.status_code == 200:
            user = resp.json().get("user", {})
            return user.get("id")
        else:
            print(f"❌ Failed to get user info: {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting user info: {e}")
        return None

def get_my_tasks(user_id):
    """Get open tasks assigned to me."""
    headers = {"Authorization": CLICKUP_API_KEY}
    
    # Get all teams
    try:
        teams_resp = requests.get(f"{BASE_URL}/team", headers=headers, timeout=10)
        if teams_resp.status_code != 200:
            print(f"❌ Failed to get teams: {teams_resp.status_code}")
            return []
        teams = teams_resp.json().get("teams", [])
        if not teams:
            print("❌ No teams found")
            return []
    except Exception as e:
        print(f"❌ Error getting teams: {e}")
        return []
    
    team_id = teams[0]["id"]
    
    # Use task endpoint with assignee filter
    all_tasks = []
    try:
        # Get spaces
        spaces_resp = requests.get(f"{BASE_URL}/team/{team_id}/space?archived=false", headers=headers, timeout=10)
        if spaces_resp.status_code != 200:
            print(f"❌ Failed to get spaces: {spaces_resp.status_code}")
            return []
        
        spaces = spaces_resp.json().get("spaces", [])
        
        for space in spaces:
            space_id = space["id"]
            
            # Get lists (folderless)
            lists_resp = requests.get(f"{BASE_URL}/space/{space_id}/list?archived=false", headers=headers, timeout=10)
            if lists_resp.status_code == 200:
                lists = lists_resp.json().get("lists", [])
                
                # Get tasks from each list
                for lst in lists:
                    tasks_resp = requests.get(
                        f"{BASE_URL}/list/{lst['id']}/task",
                        headers=headers,
                        params={
                            "assignees[]": user_id,
                            "include_closed": "false"
                        },
                        timeout=10
                    )
                    if tasks_resp.status_code == 200:
                        tasks = tasks_resp.json().get("tasks", [])
                        all_tasks.extend(tasks)
            
            # Get folders
            folders_resp = requests.get(f"{BASE_URL}/space/{space_id}/folder?archived=false", headers=headers, timeout=10)
            if folders_resp.status_code == 200:
                folders = folders_resp.json().get("folders", [])
                
                for folder in folders:
                    lists_resp = requests.get(f"{BASE_URL}/folder/{folder['id']}/list?archived=false", headers=headers, timeout=10)
                    if lists_resp.status_code == 200:
                        lists = lists_resp.json().get("lists", [])
                        
                        for lst in lists:
                            tasks_resp = requests.get(
                                f"{BASE_URL}/list/{lst['id']}/task",
                                headers=headers,
                                params={
                                    "assignees[]": user_id,
                                    "include_closed": "false"
                                },
                                timeout=10
                            )
                            if tasks_resp.status_code == 200:
                                tasks = tasks_resp.json().get("tasks", [])
                                all_tasks.extend(tasks)
    
    except Exception as e:
        print(f"❌ Error fetching tasks: {e}")
    
    return all_tasks

def get_task_comments(task_id):
    """Get all comments for a task."""
    headers = {"Authorization": CLICKUP_API_KEY}
    try:
        resp = requests.get(f"{BASE_URL}/task/{task_id}/comment", headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("comments", [])
        else:
            print(f"   ⚠️  Failed to get comments for {task_id}: {resp.status_code}")
            return []
    except Exception as e:
        print(f"   ⚠️  Error getting comments for {task_id}: {e}")
        return []

def main():
    print("🔎 ClickUp Comment Monitor")
    print(f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    if not SLACK_WEBHOOK_URL:
        print("❌ SLACK_WEBHOOK_URL not found in environment")
        return 1
    
    if not CLICKUP_API_KEY:
        print("❌ CLICKUP_API_KEY not found in environment")
        return 1
    
    # Load state
    state = load_state()
    seen_comments = state.get("seen_comments", {})
    new_alerts = 0
    
    # Get user ID
    print("\n📡 Getting user info...")
    user_id = get_my_user_id()
    if not user_id:
        print("❌ Could not get user ID")
        return 1
    print(f"   User ID: {user_id}")
    
    # Get my open tasks
    print("\n📋 Fetching assigned tasks...")
    tasks = get_my_tasks(user_id)
    print(f"   Found {len(tasks)} open tasks")
    
    # Check each task for comments
    print("\n💬 Checking for new comments...")
    for task in tasks:
        task_id = task.get("id")
        task_name = task.get("name", "Unnamed task")
        task_url = task.get("url", f"https://app.clickup.com/t/{task_id}")
        
        comments = get_task_comments(task_id)
        
        for comment in comments:
            comment_id = comment.get("id")
            
            # Skip if already seen
            if comment_id in seen_comments:
                continue
            
            # Skip if not from last 24 hours
            if not is_comment_from_last_24h(comment.get("date")):
                continue
            
            # Send alert
            print(f"\n   🆕 New comment on: {task_name[:60]}")
            if send_slack_alert(task_name, task_url, comment, SLACK_WEBHOOK_URL):
                seen_comments[comment_id] = {
                    "task_id": task_id,
                    "timestamp": comment.get("date"),
                    "alerted_at": datetime.now(timezone.utc).isoformat()
                }
                new_alerts += 1
    
    # Save state
    state['seen_comments'] = seen_comments
    state['last_check'] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    
    print(f"\n✨ Complete! {new_alerts} new alert(s) sent")
    print(f"ℹ️  Next check in 10 minutes\n")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
