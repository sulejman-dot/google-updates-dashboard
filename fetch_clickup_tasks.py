#!/usr/bin/env python3
"""
Standalone script to fetch ClickUp tasks.
This script is designed to be called by the Slack bot server.
It outputs JSON to stdout for easy parsing.

Updated: 2026-02-13 with live data from ClickUp MCP (all 37 open tasks)
"""

import json
import sys

# Live task data from ClickUp MCP (fetched 2026-02-13)
# This includes all open/active tasks assigned to Sulejman Lekovic
# Organized by status category

LIVE_TASKS = [
    # === IN PROGRESS ===
    {
        "id": "869c3ebv5",
        "name": "[bug][dashboard] Visibility discrepancy between what is shown on the dashboard and within RT",
        "status": "in progress",
        "url": "https://app.clickup.com/t/869c3ebv5",
        "customId": None,
        "assignees": ["Sulejman Lekovic", "Liviu Stoicescu"]
    },
    {
        "id": "869au7a7x",
        "name": "[bug][rt] Chart with AIO # for mobile and desktop not working - Case 2",
        "status": "in progress",
        "url": "https://app.clickup.com/t/869au7a7x",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869b23fk3",
        "name": "[improvement][rt] Improve graph colour contrast for better pattern visibility",
        "status": "in progress",
        "url": "https://app.clickup.com/t/869b23fk3",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },

    # === TO DO ===
    {
        "id": "869bwrnku",
        "name": "[bug][rt] AIO mentions metric is incorrect in competition",
        "status": "to do",
        "url": "https://app.clickup.com/t/869bwrnku",
        "customId": None,
        "assignees": ["Sulejman Lekovic", "Liviu Stoicescu"]
    },
    {
        "id": "869c42fzw",
        "name": "[bug][writer] Not enough content found error showing for the topic",
        "status": "to do",
        "url": "https://app.clickup.com/t/869c42fzw",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869c2tvk7",
        "name": "[bug][exports] Competitors ranks empty in export for branded kw",
        "status": "to do",
        "url": "https://app.clickup.com/t/869c2tvk7",
        "customId": None,
        "assignees": ["Sulejman Lekovic", "Mihai Stefan"]
    },
    {
        "id": "869c1k451",
        "name": "[improvement][rt] Improve AI fallback for restricted kw with 0 SV",
        "status": "to do",
        "url": "https://app.clickup.com/t/869c1k451",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869c1u3mj",
        "name": "[execute][looker] Custom Looker Connector for AIS and AIO data",
        "status": "to do",
        "url": "https://app.clickup.com/t/869c1u3mj",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869bt97fh",
        "name": "[improvement][writer] Improve keyword intent detection in SEO briefs",
        "status": "to do",
        "url": "https://app.clickup.com/t/869bt97fh",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "8697yqrd8",
        "name": "[feature request][forecast] Option to remove specific long-tail keywords",
        "status": "to do",
        "url": "https://app.clickup.com/t/8697yqrd8",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869btgtqc",
        "name": "Proactive Quality Assurance & CSAT Recovery",
        "status": "to do",
        "url": "https://app.clickup.com/t/869btgtqc",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },

    # === REPORTED / SHAPING ===
    {
        "id": "869c4he2x",
        "name": "[bug][writer] Topic doesn't exist notification error",
        "status": "reported",
        "url": "https://app.clickup.com/t/869c4he2x",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869bujw9p",
        "name": "[improvement][wizard] Warning for campaigns selected for China",
        "status": "reported",
        "url": "https://app.clickup.com/t/869bujw9p",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869b4rx32",
        "name": "[bug][content audit] Missing title and heading appear to have them",
        "status": "reported",
        "url": "https://app.clickup.com/t/869b4rx32",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "86988r0cv",
        "name": "[update][rt] Additional SERP features tracking",
        "status": "reported",
        "url": "https://app.clickup.com/t/86988r0cv",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "8698tbgfm",
        "name": "[update][status bar] Option to hide the status bar",
        "status": "reported",
        "url": "https://app.clickup.com/t/8698tbgfm",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "8698d1rfr",
        "name": "[update][research] Select following 10k/remaining kw in Website Explorer",
        "status": "reported",
        "url": "https://app.clickup.com/t/8698d1rfr",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "8698d0kyj",
        "name": "[update][traffic] Filtering in custom segment for conversion rate with AIO",
        "status": "reported",
        "url": "https://app.clickup.com/t/8698d0kyj",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },

    # === BACKLOG ===
    {
        "id": "869c3eftz",
        "name": "[improvement][looker] Competition Insights connector modification",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869c3eftz",
        "customId": "PRODUCT-4861",
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869c2yr03",
        "name": "[feature request][exports] Bulk export for sublocations in one CSV",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869c2yr03",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869c158h2",
        "name": "[feature request][rt] ChatGPT shopping / agentic commerce tracking",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869c158h2",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869c09eww",
        "name": "[feature request][rt] Discover AI Search kw from seed terms",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869c09eww",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869c052cu",
        "name": "[improvement][rt] Update %clicks desktop icon",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869c052cu",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869byz1nn",
        "name": "[feature request][API] Bloomreach integration with CW",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869byz1nn",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869byepjq",
        "name": "[improvement][API] Improve CW API error notification status",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869byepjq",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869bwr8px",
        "name": "[improvement][rt] Add annotation on %Clicks chart for migrated campaigns",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869bwr8px",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869bwnc4a",
        "name": "[feature request][writer] Enable article template extraction from sample URLs",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869bwnc4a",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869btrf5m",
        "name": "[improvement][rt] Improve AIO brand detection",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869btrf5m",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869bt6nx8",
        "name": "[feature request][writer] Review full keyword list before choosing topic",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869bt6nx8",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869bvwmhf",
        "name": "[improvement][writer] Prevent keyword cannibalization in SEO Briefs",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869bvwmhf",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869bt962p",
        "name": "[feature request][rt] Add notes directly on single keyword charts",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869bt962p",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869br664a",
        "name": "[feature request][API] Supporting API access for Draft Campaigns",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869br664a",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869axgewg",
        "name": "[improvement][research] Clicking + in KV navigates to adding kw instead of list",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869axgewg",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869b8etu5",
        "name": "[improvement][rt] Discuss new chart designs for AIS",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869b8etu5",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869bcjdmv",
        "name": "[feature request][looker] Implement YoY in looker reports",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869bcjdmv",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869b8cm0x",
        "name": "[feature request][rt] Expose %clicks of individual SERP features",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869b8cm0x",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
    {
        "id": "869bbjvrw",
        "name": "[feature request][API] Expose CTR and blended SERP visibility",
        "status": "backlog",
        "url": "https://app.clickup.com/t/869bbjvrw",
        "customId": None,
        "assignees": ["Sulejman Lekovic"]
    },
]


def get_open_tasks():
    """
    Fetch open ClickUp tasks assigned to Sulejman Lekovic.
    Returns tasks that are not closed or completed.
    Filters out: 'closed', 'completed'
    Shows: 'in progress', 'to do', 'reported', 'backlog', etc.
    """
    # Filter out closed and completed tasks
    excluded_statuses = ['closed', 'completed']
    open_tasks = [
        task for task in LIVE_TASKS 
        if task['status'].lower() not in excluded_statuses
    ]
    return open_tasks


def main():
    """Main entry point."""
    try:
        tasks = get_open_tasks()
        # Output as JSON
        print(json.dumps(tasks, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
