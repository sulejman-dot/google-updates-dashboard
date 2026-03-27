"""
ClickUp client for fetching tasks using the ClickUp MCP server.
This module provides a simple interface to query ClickUp tasks.
"""

import json
import subprocess
import os


class ClickUpClient:
    """Client for interacting with ClickUp via MCP."""
    
    def __init__(self):
        self.user_email = "sulejman@seomonitor.com"
        self.user_id = 81790229
    
    def get_my_open_tasks(self):
        """
        Fetch open tasks assigned to the current user.
        Returns a list of task dictionaries with simplified structure.
        """
        try:
            # Since we can't directly call MCP from a Flask subprocess,
            # we'll use a workaround: create a temporary script that uses the MCP
            # and execute it to get the results
            
            # For now, we'll use a direct approach with hardcoded data
            # In a production environment, this would use the MCP client library
            
            # Simulated task data based on real ClickUp structure
            # This should be replaced with actual MCP calls when running in an MCP-enabled environment
            tasks = self._fetch_tasks_via_search()
            
            return tasks
            
        except Exception as e:
            print(f"❌ Error in ClickUpClient.get_my_open_tasks: {e}")
            return []
    
    def _fetch_tasks_via_search(self):
        """
        Internal method to fetch tasks.
        In production, this would call the ClickUp MCP search tool.
        """
        # This is a placeholder. In a real implementation, you would:
        # 1. Use the MCP client to call mcp_clickup_clickup_search
        # 2. Parse the results
        # 3. Filter for tasks assigned to self.user_id
        # 4. Filter out closed tasks
        
        # For now, return empty list as we can't access MCP from Flask subprocess
        return []
    
    def format_task_for_slack(self, task):
        """
        Format a ClickUp task for Slack display.
        
        Args:
            task: Task dictionary from ClickUp API
            
        Returns:
            Dictionary formatted for Slack attachment
        """
        # Extract task details
        task_id = task.get('id', '')
        task_name = task.get('name', 'Untitled Task')
        task_url = task.get('url', f'https://app.clickup.com/t/{task_id}')
        status = task.get('status', 'unknown')
        custom_id = task.get('customId', '')
        assignees = task.get('assignees', [])
        
        # Build assignee string
        assignee_names = [a.get('username', '') for a in assignees if a.get('username')]
        assignee_str = ', '.join(assignee_names) if assignee_names else 'Unassigned'
        
        # Determine color based on status
        color = '#36a64f'  # green for default
        if status.lower() in ['to do', 'backlog']:
            color = '#FFA500'  # orange
        elif status.lower() == 'reported':
            color = '#e01e5a'  # red
        
        # Build Slack attachment
        attachment = {
            'color': color,
            'title': task_name,
            'title_link': task_url,
            'fields': [
                {'title': 'Status', 'value': status, 'short': True},
                {'title': 'Assignees', 'value': assignee_str, 'short': True}
            ]
        }
        
        if custom_id:
            attachment['fields'].insert(0, {'title': 'ID', 'value': custom_id, 'short': True})
        
        return attachment


# Singleton instance
_clickup_client = None

def get_clickup_client():
    """Get or create the ClickUp client singleton."""
    global _clickup_client
    if _clickup_client is None:
        _clickup_client = ClickUpClient()
    return _clickup_client
