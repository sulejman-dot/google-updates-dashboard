#!/usr/bin/env python3
"""
ClickUp Comment Monitor - Direct API Version
Uses ClickUp API directly instead of MCP library
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Import functions from the MCP integration script
from clickup_comment_monitor_mcp import load_state, save_state, process_task_comments

load_dotenv()

# Configuration
CLICKUP_API_KEY = os.getenv("CLICKUP_API_KEY", "pk_81790229_YDWXFMXHBQP0XQKK8RQCFXDNZ2LZQSQR")
CLICKUP_API_BASE = "https://api.clickup.com/api/v2"
TEAM_ID = "2179830"  # Your workspace ID

def get_assigned_tasks():
    """Fetch tasks assigned to me using ClickUp API."""
    
    headers = {
        "Authorization": CLICKUP_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Get team members to find my user ID
    team_url = f"{CLICKUP_API_BASE}/team"
    response = requests.get(team_url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Error fetching team info: {response.status_code}")
        return []
    
    team_data = response.json()
    teams = team_data.get("teams", [])
    
    if not teams:
        print("❌ No teams found")
        return []
    
    # Get tasks assigned to me
    tasks_url = f"{CLICKUP_API_BASE}/team/{TEAM_ID}/task"
    params = {
        "assignees[]": "81790229",  # Your user ID
        "include_closed": "false",
        "subtasks": "false"
    }
    
    response = requests.get(tasks_url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"❌ Error fetching tasks: {response.status_code}")
        return []
    
    tasks_data = response.json()
    tasks = tasks_data.get("tasks", [])
    
    print(f"📋 Found {len(tasks)} assigned tasks")
    return tasks


def get_task_comments(task_id):
    """Fetch comments for a specific task."""
    
    headers = {
        "Authorization": CLICKUP_API_KEY,
        "Content-Type": "application/json"
    }
    
    comments_url = f"{CLICKUP_API_BASE}/task/{task_id}/comment"
    response = requests.get(comments_url, headers=headers)
    
    if response.status_code != 200:
        return {"comments": []}
    
    return response.json()


def main():
    """Main function to check for new comments."""
    
    print(f"\n{'='*60}")
    print(f"🔔 ClickUp Comment Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Load state
    state = load_state()
    print(f"📂 Loaded state for {len(state)} tasks")
    
    # Fetch assigned tasks
    print("🔍 Fetching assigned tasks from ClickUp...")
    tasks = get_assigned_tasks()
    
    if not tasks:
        print("✅ No assigned tasks found")
        return
    
    # Process each task
    total_new_comments = 0
    for task in tasks:
        task_id = task.get("id")
        task_name = task.get("name", "Unknown Task")
        task_url = task.get("url", "")
        
        # Fetch comments
        comments_data = get_task_comments(task_id)
        
        # Process comments
        new_count = process_task_comments(
            task_id=task_id,
            task_name=task_name,
            task_url=task_url,
            comments_data=comments_data,
            state=state
        )
        total_new_comments += new_count
    
    # Save updated state
    save_state(state)
    
    print(f"\n{'='*60}")
    print(f"✅ Check complete: {total_new_comments} new comment(s) found")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
