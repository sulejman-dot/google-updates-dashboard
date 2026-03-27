#!/usr/bin/env python3
"""
Standalone script to fetch ClickUp tasks using ClickUp MCP.
This script is designed to be called by the Slack bot server.
It outputs JSON to stdout for easy parsing.
"""

import json
import sys
import subprocess


def fetch_tasks_via_mcp():
    """
    Fetch open ClickUp tasks assigned to the current user using ClickUp MCP.
    Returns list of tasks in JSON format.
    """
    try:
        # Use ClickUp MCP search to find tasks assigned to "me"
        # The MCP will automatically filter for the authenticated user
        
        # Call the MCP tool via subprocess to get tasks
        # We search for tasks in open statuses (not closed)
        result = subprocess.run([
            'npx',
            '-y',
            '@modelcontextprotocol/inspector',
            'mcp_clickup',
            'clickup_search',
            '--',
            '{"filters": {"assignees": ["me"]}, "count": 100}'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            # Fallback: Try using mcp command if inspector doesn't work
            print(json.dumps({"error": "MCP search failed", "details": result.stderr}), file=sys.stderr)
            return []
        
        # Parse MCP output
        mcp_data = json.loads(result.stdout)
        
        # Extract tasks from MCP response
        tasks = []
        if isinstance(mcp_data, dict) and 'results' in mcp_data:
            for item in mcp_data['results']:
                # Filter out closed tasks
                status = item.get('status', {}).get('status', '').lower()
                if status == 'closed':
                    continue
                
                # Extract relevant task data
                task = {
                    'id': item.get('id'),
                    'name': item.get('name'),
                    'status': status,
                    'url': item.get('url'),
                    'customId': item.get('custom_id'),
                    'assignees': [a.get('username', a.get('email', 'Unknown')) for a in item.get('assignees', [])]
                }
                tasks.append(task)
        
        return tasks
        
    except subprocess.TimeoutExpired:
        print(json.dumps({"error": "MCP call timed out"}), file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(json.dumps({"error": "Failed to parse MCP response", "details": str(e)}), file=sys.stderr)
        return []
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return []


def main():
    """Main entry point."""
    try:
        tasks = fetch_tasks_via_mcp()
        
        # If MCP fetch fails, provide helpful error
        if not tasks:
            print(json.dumps({
                "error": "No tasks found or MCP unavailable",
                "hint": "This script requires ClickUp MCP to be installed and configured"
            }), file=sys.stderr)
            return 1
        
        # Output as JSON
        print(json.dumps(tasks, indent=2))
        return 0
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
