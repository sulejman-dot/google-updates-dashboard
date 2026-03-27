#!/usr/bin/env python3
"""
ClickUp Comment Monitor - Agent-Triggered Version
This script is meant to be run by calling the Gemini agent every 5 minutes via cron
"""

import sys
import os

# Add workspace to path
workspace_dir = "/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Sulejman Workspace"
sys.path.insert(0, workspace_dir)

from clickup_comment_monitor_mcp import load_state, save_state, process_task_comments
from datetime import datetime

def main():
    """
    This script outputs a command that the Gemini agent should execute.
    The agent will use MCP to fetch tasks and comments, then process them.
    """
    
    print(f"""
🤖 ClickUp Comment Monitor - Agent Trigger
{'='*60}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

INSTRUCTIONS FOR GEMINI AGENT:
1. Use mcp_clickup_clickup_search with query: "object_type:conversations assignees:in:me"
2. For each task in results, call mcp_clickup_clickup_get_task_comments
3. For each task with comments, call:
   
   from clickup_comment_monitor_mcp import load_state, save_state, process_task_comments
   
   state = load_state()
   process_task_comments(
       task_id=<task_id>,
       task_name=<task_name>,
       task_url=<task_url>,
       comments_data=<comments_data>,
       state=state
   )
   save_state(state)

This will check for new comments and send Slack notifications.
{'='*60}
    """)

if __name__ == "__main__":
    main()
