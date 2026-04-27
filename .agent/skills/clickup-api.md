# ClickUp API — Agent Instructions

You are being given access to the SEOmonitor ClickUp workspace via the ClickUp REST API. This document tells you how to authenticate, what endpoints are available, and how to use them.

---

## Authentication Setup

Before you can call the ClickUp API, the user must provide a personal API token.

### Ask the user to generate their token:

> To use ClickUp through me, you'll need a personal API token. Here's how to get one:
>
> 1. Open ClickUp in your browser
> 2. Click your **avatar** (bottom-left)
> 3. Go to **Settings** → **Apps**
> 4. Copy your **API Token** (or click Generate if there isn't one)

### How the token should be provided to you:

**Preferred (token stays hidden from conversation):**

- If you have access to a **terminal or shell**: ask the user to set an environment variable. Then reference `$CLICKUP_API_KEY` in your commands — you never need to see the actual value.

  > Please run this in your terminal (paste your token in place of `xxx`):
  > ```
  > export CLICKUP_API_KEY=xxx
  > ```
  > I'll use `$CLICKUP_API_KEY` in my commands so I never see your token directly.

- If you are a **custom GPT, plugin, or tool with a dedicated auth/secrets configuration**: ask the user to paste the token in that configuration area, not in the chat.

- If you are configured via an **MCP server or similar tool layer**: the token should be set in your server configuration, not passed through the conversation.

**Fallback (if none of the above apply):**

If you are a plain chat agent with no tool execution, shell access, or secrets store, the user will need to include the token in messages for you to construct API calls. In this case, warn them:

> I don't have a way to store secrets separately from our conversation. If you paste your token here, I'll be able to see it. If that's OK, go ahead — but be aware this is less secure. You can always regenerate the token later in ClickUp Settings → Apps.

---

## API Reference

### Base URL
```
https://api.clickup.com/api/v2
```

### Headers (every request)
```
Authorization: {token}
Content-Type: application/json
```

The token goes directly as the value — no "Bearer" prefix.

### SEOmonitor Workspace ID
```
2179830
```

Use this for any workspace-level endpoint (search, listing spaces, etc.).

---

## Endpoints

### Get a Task
```
GET /task/{task_id}
```

Task IDs are the short alphanumeric codes in ClickUp URLs. Example: `https://app.clickup.com/t/86a1b2c3d` → task ID is `86a1b2c3d`.

Returns: name, description, status, assignees, due date, tags, custom fields, priority, dates.

### Search Tasks
```
GET /team/2179830/task
```

Query parameters:
- `statuses[]` — e.g., `open`, `in progress`, `closed`
- `list_ids[]` — filter to specific list(s)
- `assignees[]` — ClickUp user IDs
- `tags[]` — tag names
- `order_by` — `created`, `updated`, `due_date`
- `include_closed` — `true` to include completed tasks

### Get Tasks in a List
```
GET /list/{list_id}/task
```

### Get Task Comments
```
GET /task/{task_id}/comment
```

### Post a Comment
```
POST /task/{task_id}/comment

{"comment_text": "Your message here"}
```

### Update a Task
```
PUT /task/{task_id}

{"status": "in progress", "priority": 2}
```

Updatable fields: `status`, `name`, `description`, `priority` (1=Urgent, 2=High, 3=Normal, 4=Low), `due_date` (unix ms), `assignees` (object with `add`/`rem` arrays of user IDs).

### Create a Task
```
POST /list/{list_id}/task

{
  "name": "Task name",
  "description": "Details",
  "status": "open",
  "priority": 3
}
```

### Browse Workspace Structure

To discover spaces, folders, lists, and their IDs:

```
GET /team/2179830/space          → lists all spaces
GET /space/{space_id}/folder     → folders in a space
GET /folder/{folder_id}/list     → lists in a folder
GET /space/{space_id}/list       → lists not in any folder
```

### Get Workspace Members
```
GET /team/2179830
```

The `members` array in the response contains user IDs and names.

---

## Example: Full curl Command

If you have shell access, construct calls like this:

```bash
curl -s "https://api.clickup.com/api/v2/task/86a1b2c3d" \
  -H "Authorization: $CLICKUP_API_KEY" \
  -H "Content-Type: application/json"
```

The `$CLICKUP_API_KEY` environment variable keeps the token out of the conversation.

---

## Rate Limits

~100 requests per minute per token. Sufficient for normal usage. If you need to fetch many tasks, use search with filters rather than fetching one by one.

---

## Tips

- Always check if a task exists before trying to update it.
- Use search with filters rather than listing entire spaces — it's faster and avoids pagination.
- When the user shares a ClickUp URL, extract the task ID from it (last path segment).
- Dates in the API are unix timestamps in milliseconds.
- The full API reference is at: https://clickup.com/api/
