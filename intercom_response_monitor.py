#!/usr/bin/env python3
"""
Intercom Response Time Monitor - MCP Integration

Monitors open Intercom conversations and alerts when no team reply for 15+ minutes.
Uses Intercom MCP (no API token needed).
"""

import os
import json
from datetime import datetime, timedelta
from slack_sdk import WebClient
from dotenv import load_dotenv

load_dotenv()

# Configuration
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN") or "xoxb-4173116321-10452138701364-22v7lSrQNCFqFe6lX8g0aCXM"
SLACK_ALERT_CHANNEL = os.getenv("SLACK_ALERT_CHANNEL", "#cx-team-chat")
STATE_FILE = "intercom_alert_state.json"
RESPONSE_THRESHOLD_MINUTES = 10

slack_client = WebClient(token=SLACK_BOT_TOKEN)


def load_state():
    """Load the state of conversations we've already alerted on."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading state file: {e}")
            return {}
    return {}


def save_state(state):
    """Save the current alert state to file."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"💾 State saved to {STATE_FILE}")
    except Exception as e:
        print(f"❌ Error saving state: {e}")


def send_slack_alert(conversation_id, title, customer_name, waiting_minutes, assignee, conv_url):
    """Send a Slack notification for a conversation waiting for reply."""
    
    try:
        # Build assignee text
        assignee_text = assignee if assignee else "Unassigned"
        
        # Build message
        message = {
            "channel": SLACK_ALERT_CHANNEL,
            "text": f"🚨 Intercom: No Reply for {waiting_minutes} Minutes",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 Intercom: No Reply for {waiting_minutes} Minutes"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Conversation:*\n{title[:100]}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Customer:*\n{customer_name}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Waiting:*\n{waiting_minutes} minutes"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Assignee:*\n{assignee_text}"
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
                                "text": "View Conversation"
                            },
                            "url": conv_url,
                            "style": "danger"
                        }
                    ]
                }
            ]
        }
        
        slack_client.chat_postMessage(**message)
        print(f"✅ Sent alert for conversation: {conversation_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending Slack alert: {e}")
        return False


def check_conversation_response_time(conv_data, state):
    """
    Check if conversation needs an alert based on response time.
    
    Args:
        conv_data: Full conversation data from Intercom MCP
        state: Current alert state dict
    
    Returns:
        True if alert was sent, False otherwise
    """
    try:
        conv_id = conv_data.get('id', '').replace('conversation_', '')
        
        # Skip if we've already alerted on this conversation
        if conv_id in state:
            print(f"⏭️  Skipping {conv_id} - already alerted")
            return False
        
        # Get conversation parts (messages)
        parts = conv_data.get('conversation_parts', {}).get('conversation_parts', [])
        
        if not parts:
            print(f"⏭️  No parts found for {conv_id}")
            return False
        
        # Find the last customer message and check if team replied after
        last_customer_time = None
        team_replied_after = False
        
        # Sort parts by created_at (oldest first)
        sorted_parts = sorted(parts, key=lambda x: int(x.get('created_at', 0)))
        
        for part in sorted_parts:
            part_type = part.get('part_type', '')
            author_type = part.get('author', {}).get('type', '')
            created_at = int(part.get('created_at', 0))
            
            # Track customer messages
            if author_type == 'user' or part_type == 'conversation':
                last_customer_time = created_at
                team_replied_after = False  # Reset flag
            
            # Track team replies (admin or bot replies)
            elif author_type in ['admin', 'bot'] and part_type in ['comment', 'note']:
                if last_customer_time:
                    team_replied_after = True
        
        # If team has replied after last customer message, no alert needed
        if team_replied_after or not last_customer_time:
            return False
        
        # Calculate time since last customer message
        now = datetime.now()
        last_msg_time = datetime.fromtimestamp(last_customer_time)
        time_diff = now - last_msg_time
        waiting_minutes = int(time_diff.total_seconds() / 60)
        
        # Check if waiting time exceeds threshold
        if waiting_minutes >= RESPONSE_THRESHOLD_MINUTES:
            # Extract conversation details
            title = conv_data.get('title', 'Untitled Conversation')
            source = conv_data.get('source', {})
            customer = source.get('author', {})
            customer_name = customer.get('name', customer.get('email', 'Unknown'))
            
            # Get assignee
            assignee = None
            admin = conv_data.get('assignee', {})
            if admin and admin.get('type') == 'admin':
                assignee = admin.get('name', 'Unknown Admin')
            
            # Get conversation URL
            conv_url = f"https://app.intercom.com/a/inbox/_/inbox/conversation/{conv_id}"
            
            # Send alert
            if send_slack_alert(conv_id, title, customer_name, waiting_minutes, assignee, conv_url):
                # Mark as alerted
                state[conv_id] = {
                    'alerted_at': now.isoformat(),
                    'waiting_minutes': waiting_minutes,
                    'title': title[:100]
                }
                save_state(state)
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error checking conversation: {e}")
        import traceback
        traceback.print_exc()
        return False


def process_conversations(conversations_data):
    """
    Process a list of conversations and send alerts as needed.
    
    Args:
        conversations_data: List of conversation data from Intercom MCP search
    
    Returns:
        Number of alerts sent
    """
    state = load_state()
    alerts_sent = 0
    
    print(f"\n🔍 Processing {len(conversations_data)} open conversations...")
    
    for conv in conversations_data:
        if check_conversation_response_time(conv, state):
            alerts_sent += 1
    
    print(f"\n✅ Completed. Sent {alerts_sent} alert(s).\n")
    return alerts_sent


# This script is designed to be called by the Gemini agent with MCP data
if __name__ == "__main__":
    print("""
🚀 Intercom Response Time Monitor - MCP Integration

This script is designed to be used by the Gemini agent with MCP access.

The agent will:
1. Search for open Intercom conversations using MCP
2. Get full conversation details for each
3. Call process_conversations() to check response times
4. Send Slack alerts for conversations waiting 15+ minutes

To run the monitor, ask the Gemini agent to check Intercom response times.
    """)
