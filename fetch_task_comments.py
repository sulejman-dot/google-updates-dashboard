#!/usr/bin/env python3
"""
Fetch comments for a specific ClickUp task using MCP.
Usage: python3 fetch_task_comments.py <task_id>
Outputs JSON to stdout.
"""

import sys
import json
import os

# This script is designed to be called by the Slack bot
# It uses the ClickUp MCP to fetch comments for a specific task

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Task ID required"}), file=sys.stderr)
        sys.exit(1)
    
    task_id = sys.argv[1]
    
    # Import MCP client
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        import asyncio
    except ImportError:
        # Fallback: use direct API call
        import requests
        
        api_key = os.getenv("CLICKUP_API_KEY", "pk_81790229_YDWXFMXHBQP0XQKK8RQCFXDNZ2LZQSQR")
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
        
        url = f"https://api.clickup.com/api/v2/task/{task_id}/comment"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            print(json.dumps(response.json()))
            sys.exit(0)
        else:
            print(json.dumps({"comments": []}))
            sys.exit(0)
    
    # Use MCP to fetch comments
    async def fetch_comments():
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-clickup"],
            env={
                **os.environ,
                "CLICKUP_API_KEY": os.getenv("CLICKUP_API_KEY", ""),
            }
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "clickup_get_task_comments",
                    arguments={"task_id": task_id}
                )
                
                if result and result.content:
                    comments_data = json.loads(result.content[0].text)
                    print(json.dumps(comments_data))
                else:
                    print(json.dumps({"comments": []}))
    
    asyncio.run(fetch_comments())

if __name__ == "__main__":
    main()
