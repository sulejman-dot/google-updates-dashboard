---
description: Check for new ClickUp comments and send Slack notifications
---

# ClickUp Comment Monitor Workflow

Check all your open ClickUp tasks for new comments posted in the last 24 hours and send Slack alerts.

## Steps

1. **Load the state file** to track which comments have already been alerted
   - State file: `clickup_comment_state.json`
   - Contains: `last_check` timestamp and `seen_comments` dict

2. **Search for your open tasks** using MCP ClickUp
   - Use `mcp_clickup_clickup_search` with filters:
     - `filters.assignees`: Your user ID (find via `mcp_clickup_clickup_get_workspace_members`)
     - `filters.task_statuses`: ["unstarted", "active"] (exclude "done", "closed", "archived")
   - This returns task IDs, names, URLs, and status

3. **For each open task, fetch comments** using MCP ClickUp
   - Use `mcp_clickup_clickup_get_task_comments` with the task ID
   - This returns all comments with timestamps, users, and content

4. **Filter for new comments from the last 24 hours**
   - Check comment timestamp (convert from milliseconds to datetime)
   - Skip comments older than 24 hours
   - Skip comments already in `seen_comments` state

5. **Send Slack alerts for new comments**
   - Use the Slack webhook URL from `.env` file
   - Format: Task name, commenter, timestamp, comment preview
   - Include link to the task

6. **Update the state file**
   - Add newly alerted comment IDs to `seen_comments`
   - Update `last_check` timestamp
   - Save to `clickup_comment_state.json`

7. **Summary**
   - Report how many tasks checked
   - Report how many new comments found
   - Report how many alerts sent

## Expected Output

```
🔎 ClickUp Comment Monitor
📋 Checked 15 open tasks
💬 Found 3 new comments
✅ Sent 3 Slack alerts
```

## Notes

- This workflow is designed to be run every 10 minutes by a LaunchAgent
- Comments are only alerted once (tracked in state file)
- Only checks tasks assigned to you
- Only alerts on comments from the last 24 hours
