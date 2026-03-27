#!/usr/bin/env python3
"""
Setup script to register a ClickUp webhook for task comment notifications.
This version uses environment variables and provides clear instructions.
"""

import os
import requests
import json

# Get ngrok URL
NGROK_URL = input("Enter your ngrok URL (e.g., https://abc123.ngrok-free.dev): ").strip()

# Get ClickUp API token
print("\n📋 To get your ClickUp API token:")
print("   1. Go to https://app.clickup.com/settings/apps")
print("   2. Click 'Generate' under 'API Token'")
print("   3. Copy the token")
print()

CLICKUP_API_TOKEN = input("Paste your ClickUp API token: ").strip()

if not CLICKUP_API_TOKEN:
    print("❌ Error: API token is required")
    exit(1)

# Get team/workspace ID
print("\n🔍 Fetching your ClickUp workspaces...")

headers = {
    "Authorization": CLICKUP_API_TOKEN,
    "Content-Type": "application/json"
}

try:
    resp = requests.get("https://api.clickup.com/api/v2/team", headers=headers)
    resp.raise_for_status()
    teams = resp.json().get("teams", [])
    
    if not teams:
        print("❌ No teams found. Please check your API token.")
        exit(1)
    
    print("\n📋 Available Workspaces:")
    for i, team in enumerate(teams, 1):
        print(f"{i}. {team['name']} (ID: {team['id']})")
    
    if len(teams) == 1:
        choice = 0
        print(f"\n✅ Auto-selected: {teams[0]['name']}")
    else:
        choice = int(input("\nSelect workspace number: ")) - 1
    
    CLICKUP_TEAM_ID = teams[choice]['id']
    print(f"✅ Using workspace: {teams[choice]['name']} (ID: {CLICKUP_TEAM_ID})")
    
except Exception as e:
    print(f"❌ Error fetching workspaces: {e}")
    exit(1)

# Get Slack channel for notifications
print("\n💬 Where should notifications be sent?")
SLACK_CHANNEL = input("Enter Slack channel or user ID (e.g., #general or @username): ").strip() or "#general"

# Webhook configuration
webhook_endpoint = f"{NGROK_URL}/clickup/webhook"

webhook_payload = {
    "endpoint": webhook_endpoint,
    "events": [
        "taskCommentPosted"
    ]
}

print(f"\n🔧 Registering webhook...")
print(f"   Endpoint: {webhook_endpoint}")
print(f"   Events: taskCommentPosted")
print(f"   Notifications will be sent to: {SLACK_CHANNEL}")

try:
    # Create webhook
    url = f"https://api.clickup.com/api/v2/team/{CLICKUP_TEAM_ID}/webhook"
    resp = requests.post(url, headers=headers, json=webhook_payload)
    resp.raise_for_status()
    
    webhook_data = resp.json()
    webhook_id = webhook_data.get("id")
    
    print(f"\n✅ Webhook created successfully!")
    print(f"   Webhook ID: {webhook_id}")
    print(f"   Status: {webhook_data.get('status', 'active')}")
    
    # Save configuration to .env
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    
    # Read existing .env
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key] = value
    
    # Update with new values
    env_vars["CLICKUP_API_TOKEN"] = CLICKUP_API_TOKEN
    env_vars["CLICKUP_TEAM_ID"] = CLICKUP_TEAM_ID
    env_vars["CLICKUP_WEBHOOK_ID"] = webhook_id
    env_vars["SLACK_ALERT_CHANNEL"] = SLACK_CHANNEL
    
    # Write back to .env
    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"💾 Saved configuration to .env file")
    
    print("\n🎉 Setup complete! You'll now receive Slack notifications when someone comments on your ClickUp tasks.")
    print("\n📝 To test:")
    print("   1. Go to any ClickUp task where you're assigned")
    print("   2. Add a comment")
    print("   3. Check your Slack for the notification")
    print("\n⚠️  Note: Remember to restart your Slack bot server to load the new .env variables!")
    
except requests.exceptions.HTTPError as e:
    print(f"\n❌ Error creating webhook: {e}")
    print(f"Response: {e.response.text}")
    
    # Check if webhook already exists
    if e.response.status_code == 400:
        print("\n💡 A webhook might already exist. Listing existing webhooks...")
        try:
            list_url = f"https://api.clickup.com/api/v2/team/{CLICKUP_TEAM_ID}/webhook"
            resp = requests.get(list_url, headers=headers)
            resp.raise_for_status()
            webhooks = resp.json().get("webhooks", [])
            
            if webhooks:
                print(f"\n📋 Found {len(webhooks)} existing webhook(s):")
                for wh in webhooks:
                    print(f"   - ID: {wh['id']}")
                    print(f"     Endpoint: {wh['endpoint']}")
                    print(f"     Events: {', '.join(wh['events'])}")
                    print(f"     Status: {wh.get('status', 'unknown')}")
                    print()
                    
                # Ask if user wants to delete and recreate
                delete = input("Delete existing webhook and create new one? (y/n): ").lower()
                if delete == 'y' and webhooks:
                    for wh in webhooks:
                        delete_url = f"https://api.clickup.com/api/v2/webhook/{wh['id']}"
                        del_resp = requests.delete(delete_url, headers=headers)
                        if del_resp.status_code == 200:
                            print(f"✅ Deleted webhook {wh['id']}")
                    print("\n🔄 Please run this script again to create a new webhook.")
            else:
                print("   No existing webhooks found.")
        except Exception as list_error:
            print(f"   Error listing webhooks: {list_error}")
            
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
