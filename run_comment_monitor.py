#!/usr/bin/env python3
"""
Standalone ClickUp Comment Monitor Runner
This script can be scheduled with cron to run every 5 minutes.
"""

import sys
import os
import json
from datetime import datetime

# Add the workspace directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the MCP-based monitor functions
from clickup_comment_monitor_mcp import load_state, save_state, process_task_comments

# ClickUp MCP integration
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    import asyncio
except ImportError:
    print("❌ MCP library not found. Install with: pip install mcp")
    sys.exit(1)


async def get_clickup_tasks_and_comments():
    """Fetch tasks and comments using ClickUp MCP."""
    
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-clickup"],
        env={
            **os.environ,
            "CLICKUP_API_KEY": os.getenv("CLICKUP_API_KEY", ""),
        }
    )
    
    tasks_with_comments = []
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Search for assigned tasks
            search_result = await session.call_tool(
                "clickup_search",
                arguments={"query": "object_type:conversations assignees:in:me"}
            )
            
            if not search_result or not search_result.content:
                print("⚠️  No search results from ClickUp")
                return tasks_with_comments
            
            # Parse search results
            search_data = json.loads(search_result.content[0].text)
            tasks = search_data.get("results", [])
            
            print(f"📋 Found {len(tasks)} assigned tasks")
            
            # Get comments for each task
            for task in tasks:
                if task.get("type") != "task":
                    continue
                
                task_id = task.get("id")
                task_name = task.get("name", "Unknown Task")
                task_url = task.get("url", "")
                
                # Fetch comments
                try:
                    comments_result = await session.call_tool(
                        "clickup_get_task_comments",
                        arguments={"task_id": task_id}
                    )
                    
                    if comments_result and comments_result.content:
                        comments_data = json.loads(comments_result.content[0].text)
                        
                        tasks_with_comments.append({
                            "task_id": task_id,
                            "task_name": task_name,
                            "task_url": task_url,
                            "comments": comments_data
                        })
                except Exception as e:
                    print(f"⚠️  Error fetching comments for {task_name}: {e}")
                    continue
    
    return tasks_with_comments


async def main():
    """Main function to check for new comments and send notifications."""
    
    print(f"\n{'='*60}")
    print(f"🔔 ClickUp Comment Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Load state
    state = load_state()
    print(f"📂 Loaded state for {len(state)} tasks")
    
    # Fetch tasks and comments
    print("🔍 Fetching tasks and comments from ClickUp...")
    tasks_with_comments = await get_clickup_tasks_and_comments()
    
    if not tasks_with_comments:
        print("✅ No tasks with comments found")
        return
    
    # Process each task
    total_new_comments = 0
    for task_data in tasks_with_comments:
        new_count = process_task_comments(
            task_id=task_data["task_id"],
            task_name=task_data["task_name"],
            task_url=task_data["task_url"],
            comments_data=task_data["comments"],
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
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
