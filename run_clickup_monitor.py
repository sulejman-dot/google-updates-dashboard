#!/usr/bin/env python3
"""
ClickUp Comment Monitor Runner
Fetches data from ClickUp API and processes alerts
"""

import os
import json
import sys
from dotenv import load_dotenv
from clickup_slack_alert import process_tasks_and_comments

# Load environment variables
load_dotenv()

def fetch_clickup_data():
    """Fetch tasks and comments using ClickUp API"""
    import requests
    
    api_key = os.getenv("CLICKUP_API_KEY")
    if not api_key:
        print("❌ CLICKUP_API_KEY not found in environment")
        return None, None
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    # Get workspace/team ID (you may need to adjust this)
    # For now, we'll search across all accessible tasks
    base_url = "https://api.clickup.com/api/v2"
    
    # Get teams
    teams_resp = requests.get(f"{base_url}/team", headers=headers)
    if teams_resp.status_code != 200:
        print(f"❌ Failed to get teams: {teams_resp.status_code}")
        return None, None
    
    teams = teams_resp.json().get("teams", [])
    if not teams:
        print("❌ No teams found")
        return None, None
    
    team_id = teams[0]["id"]
    print(f"Using team: {teams[0]['name']} (ID: {team_id})")
    
    # Search for tasks assigned to sulejman@seomonitor.com
    # Get spaces first
    spaces_resp = requests.get(f"{base_url}/team/{team_id}/space", headers=headers)
    if spaces_resp.status_code != 200:
        print(f"❌ Failed to get spaces: {spaces_resp.status_code}")
        return None, None
    
    spaces = spaces_resp.json().get("spaces", [])
    
    # Collect all tasks from all lists
    all_tasks = []
    for space in spaces:
        space_id = space["id"]
        # Get folders
        folders_resp = requests.get(f"{base_url}/space/{space_id}/folder", headers=headers)
        folders = folders_resp.json().get("folders", [])
        
        # Get folderless lists
        lists_resp = requests.get(f"{base_url}/space/{space_id}/list", headers=headers)
        lists = lists_resp.json().get("lists", [])
        
        # Get lists from folders
        for folder in folders:
            folder_lists_resp = requests.get(f"{base_url}/folder/{folder['id']}/list", headers=headers)
            lists.extend(folder_lists_resp.json().get("lists", []))
        
        # Get tasks from each list
        for lst in lists:
            list_id = lst["id"]
            tasks_resp = requests.get(
                f"{base_url}/list/{list_id}/task",
                headers=headers,
                params={
                    "assignees[]": "sulejman@seomonitor.com",
                    "include_closed": False
                }
            )
            if tasks_resp.status_code == 200:
                tasks = tasks_resp.json().get("tasks", [])
                all_tasks.extend(tasks)
    
    print(f"✅ Found {len(all_tasks)} tasks")
    
    # Fetch comments for each task
    comments_by_task = {}
    for task in all_tasks:
        task_id = task["id"]
        comments_resp = requests.get(
            f"{base_url}/task/{task_id}/comment",
            headers=headers
        )
        if comments_resp.status_code == 200:
            comments_by_task[task_id] = comments_resp.json()
    
    print(f"✅ Fetched comments for {len(comments_by_task)} tasks")
    
    # Format as expected by process_tasks_and_comments
    tasks_data = {"results": all_tasks}
    
    return tasks_data, comments_by_task

def main():
    print("🔎 ClickUp Comment Monitor - Starting scan...")
    
    try:
        # Fetch data from ClickUp
        print("\n📡 Fetching tasks and comments from ClickUp...")
        tasks_data, comments_by_task = fetch_clickup_data()
        
        if not tasks_data or not comments_by_task:
            print("❌ Failed to fetch data")
            return
        
        # Process and send alerts
        print("\n🔍 Processing comments for new alerts...")
        
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            print("❌ SLACK_WEBHOOK_URL not found in environment")
            return
        
        dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
        
        alerts_sent = process_tasks_and_comments(
            tasks_data,
            comments_by_task,
            webhook_url,
            dry_run=dry_run
        )
        
        print(f"\n✨ Complete! {alerts_sent} alert(s) processed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
