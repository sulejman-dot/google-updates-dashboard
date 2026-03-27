---
description: Refresh ClickUp dashboard data via MCP and deploy to Netlify
---

# Refresh ClickUp Dashboard

Pulls fresh task data from ClickUp via MCP, updates `clickup_data.json`, commits and pushes to trigger Netlify deploy.

## Steps

1. Search for all open/active tasks from ClickUp Maintenance list:

```
Use mcp_clickup_clickup_search with:
- keywords: "" (empty to get all)
- filters: { asset_types: ["task"], task_statuses: ["active", "unstarted"] }
- count: 50
- sort: [{ field: "updated_at", direction: "desc" }]

Also search for recently closed tasks:
- filters: { asset_types: ["task"], task_statuses: ["done", "closed"] }
- count: 50

Run searches for keywords: "bug", "improvement", "investigate", "feature" to capture all tasks.
Only include tasks where hierarchy.subcategory.name == "SEOmonitor: Maintenance"
```

2. Process all results and build dashboard JSON with:
   - Status distribution (to do, in progress, reported, closed, backlog)
   - Workload per team member (open tasks only)
   - Task types: [bug], [improvement], [investigate], [feature request]
   - Module breakdown: parse 2nd bracket from task name [type][module]
   - KPI summary: total_open, in_progress, todo_reported, closed_recent

3. Write the processed data to:
   `/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Sulejman Workspace/clickup-dashboard/clickup_data.json`

4. Commit and push to deploy:
// turbo
```bash
cd "/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Sulejman Workspace/clickup-dashboard"
git add clickup_data.json
git diff --cached --quiet || git commit -m "🔄 Refresh ClickUp data — $(date +'%Y-%m-%d %H:%M')"
git push
```
