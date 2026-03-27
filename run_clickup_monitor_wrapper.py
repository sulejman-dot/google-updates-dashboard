#!/usr/bin/env python3
"""
ClickUp Comment Monitor - Calls Antigravity workflow
This script runs every 10 minutes via LaunchAgent and triggers the workflow
"""

import os
import sys
import subprocess
from datetime import datetime, timezone

def main():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"🔎 ClickUp Comment Monitor - {timestamp}")
    
    # Path to Antigravity CLI (adjust if needed)
    # This assumes you have Antigravity installed and accessible
    workspace_dir = "/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Sulejman Workspace"
    
    # Call the workflow using Python subprocess
    # We'll run the clickup_slack_alert.py script designed for MCP
    script_path = os.path.join(workspace_dir, "clickup_monitor_complete.py")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr, file=sys.stderr)
        
        if result.returncode != 0:
            print(f"❌ Script failed with exit code {result.returncode}", file=sys.stderr)
            return 1
        
        print("✅ Monitor check complete")
        
    except subprocess.TimeoutExpired:
        print("❌ Script timed out after 5 minutes", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error running monitor: {e}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
