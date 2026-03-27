#!/usr/bin/env python3
"""
ClickUp Comment Monitor - MCP Integration Script

This script is designed to be run by the Gemini agent which has access to ClickUp MCP.
It fetches tasks and comments using MCP, then checks for new comments and sends Slack notifications.

Usage: Run this script through the Gemini agent, not standalone.
"""

import os
import json
from datetime import datetime
from slack_sdk import WebClient
from dotenv import load_dotenv

load_dotenv()

# Configuration
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN") or "xoxb-4173116321-10452138701364-22v7lSrQNCFqFe6lX8g0aCXM"
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
        print(f"💾 State saved to {STATE_FILE}")
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


def process_task_comments(task_id, task_name, task_url, comments_data, state):
    """
    Process comments for a single task and send notifications for new ones.
    
    Args:
        task_id: ClickUp task ID
        task_name: Task name
        task_url: Task URL
        comments_data: Comments data from ClickUp MCP (dict with 'comments' list)
        state: Current state dict
    
    Returns:
        Number of new comments found
    """
    comments = comments_data.get('comments', [])
    
    if not comments:
        return 0
    
    # Get the last seen comment ID for this task
    task_state = state.get(task_id, {})
    last_seen_id = task_state.get('last_comment_id')
    
    # Find new comments
    new_comments = []
    latest_comment_id = None
    
    for comment in comments:
        comment_id = comment.get('id')
        
        # Track the latest comment
        if not latest_comment_id:
            latest_comment_id = comment_id
        
        # If we haven't seen this comment before, it's new
        if last_seen_id and comment_id == last_seen_id:
            break  # Stop when we reach the last seen comment
        
        new_comments.append(comment)
    
    # Send notifications for new comments (oldest first)
    new_count = 0
    for comment in reversed(new_comments):
        commenter = comment.get('user', {})
        commenter_name = commenter.get('username', 'Unknown User')
        comment_text = comment.get('comment_text', comment.get('text', ''))
        comment_date = comment.get('date', '')
        
        # Convert timestamp to readable format
        if comment_date:
            try:
                timestamp = int(comment_date) / 1000
                comment_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
            except:
                comment_date = 'Unknown time'
        
        send_slack_notification(
            task_name=task_name,
            task_url=task_url,
            commenter_name=commenter_name,
            comment_text=comment_text,
            comment_date=comment_date
        )
        new_count += 1
    
    # Update state for this task
    if latest_comment_id:
        state[task_id] = {
            'last_comment_id': latest_comment_id,
            'last_check': datetime.now().isoformat(),
            'task_name': task_name
        }
    
    return new_count


# This script is designed to be imported and used by the Gemini agent
# The agent will call process_task_comments() with MCP data

if __name__ == "__main__":
    print("""
🚀 ClickUp Comment Monitor - MCP Integration

This script is designed to be used by the Gemini agent with MCP access.

The agent will:
1. Search for your assigned tasks using ClickUp MCP
2. Get comments for each task using ClickUp MCP
3. Call process_task_comments() to check for new comments
4. Send Slack notifications for any new comments found

To run the monitor, ask the Gemini agent to execute the comment check.
    """)
