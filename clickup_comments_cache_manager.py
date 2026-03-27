#!/usr/bin/env python3
"""
ClickUp Comments Cache Builder
Generates a JSON cache of all comments across monitored tasks.
Called by the cron script to keep the cache fresh.
The Slack bot reads this cache to show daily comment summaries.
"""

import json
import os
import sys
import requests
from datetime import datetime

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(WORKSPACE_DIR, "clickup_comments_cache.json")

# Task IDs and info — all open (non-closed) tasks assigned to Sulejman
# Last synced: 2026-02-13
MONITORED_TASKS = {
    # === IN PROGRESS ===
    "869c3ebv5": {"name": "[bug][dashboard] Visibility discrepancy between dashboard and RT", "url": "https://app.clickup.com/t/869c3ebv5"},
    "869au7a7x": {"name": "[bug][rt] Chart with AIO # for mobile and desktop not working - Case 2", "url": "https://app.clickup.com/t/869au7a7x"},
    "869b23fk3": {"name": "[improvement][rt] Improve graph colour contrast for better pattern visibility", "url": "https://app.clickup.com/t/869b23fk3"},
    # === TO DO ===
    "869bwrnku": {"name": "[bug][rt] AIO mentions metric is incorrect in competition", "url": "https://app.clickup.com/t/869bwrnku"},
    "869c42fzw": {"name": "[bug][writer] Not enough content found error showing for the topic", "url": "https://app.clickup.com/t/869c42fzw"},
    "869c2tvk7": {"name": "[bug][exports] Competitors ranks empty in export for branded kw", "url": "https://app.clickup.com/t/869c2tvk7"},
    "869c1k451": {"name": "[improvement][rt] Improve AI fallback for restricted kw with 0 SV", "url": "https://app.clickup.com/t/869c1k451"},
    "869c1u3mj": {"name": "[execute][looker] Custom Looker Connector for AIS and AIO data", "url": "https://app.clickup.com/t/869c1u3mj"},
    "869bt97fh": {"name": "[improvement][writer] Improve keyword intent detection in SEO briefs", "url": "https://app.clickup.com/t/869bt97fh"},
    "8697yqrd8": {"name": "[feature request][forecast] Option to remove specific long-tail keywords", "url": "https://app.clickup.com/t/8697yqrd8"},
    "869btgtqc": {"name": "Proactive Quality Assurance & CSAT Recovery", "url": "https://app.clickup.com/t/869btgtqc"},
    # === REPORTED / SHAPING ===
    "869c4he2x": {"name": "[bug][writer] Topic doesn't exist notification error", "url": "https://app.clickup.com/t/869c4he2x"},
    "869bujw9p": {"name": "[improvement][wizard] Warning for campaigns selected for China", "url": "https://app.clickup.com/t/869bujw9p"},
    "869b4rx32": {"name": "[bug][content audit] Missing title and heading appear to have them", "url": "https://app.clickup.com/t/869b4rx32"},
    "86988r0cv": {"name": "[update][rt] Additional SERP features tracking", "url": "https://app.clickup.com/t/86988r0cv"},
    "8698tbgfm": {"name": "[update][status bar] Option to hide the status bar", "url": "https://app.clickup.com/t/8698tbgfm"},
    "8698d1rfr": {"name": "[update][research] Select following 10k/remaining kw in Website Explorer", "url": "https://app.clickup.com/t/8698d1rfr"},
    "8698d0kyj": {"name": "[update][traffic] Filtering in custom segment for conversion rate with AIO", "url": "https://app.clickup.com/t/8698d0kyj"},
    # === BACKLOG (product feedback) ===
    "869c3eftz": {"name": "[improvement][looker] Competition Insights connector modification", "url": "https://app.clickup.com/t/869c3eftz"},
    "869c2yr03": {"name": "[feature request][exports] Bulk export for sublocations in one CSV", "url": "https://app.clickup.com/t/869c2yr03"},
    "869c158h2": {"name": "[feature request][rt] ChatGPT shopping / agentic commerce tracking", "url": "https://app.clickup.com/t/869c158h2"},
    "869c09eww": {"name": "[feature request][rt] Discover AI Search kw from seed terms", "url": "https://app.clickup.com/t/869c09eww"},
    "869c052cu": {"name": "[improvement][rt] Update %clicks desktop icon", "url": "https://app.clickup.com/t/869c052cu"},
    "869byz1nn": {"name": "[feature request][API] Bloomreach integration with CW", "url": "https://app.clickup.com/t/869byz1nn"},
    "869byepjq": {"name": "[improvement][API] Improve CW API error notification status", "url": "https://app.clickup.com/t/869byepjq"},
    "869bwr8px": {"name": "[improvement][rt] Add annotation on %Clicks chart for migrated campaigns", "url": "https://app.clickup.com/t/869bwr8px"},
    "869bwnc4a": {"name": "[feature request][writer] Enable article template extraction from sample URLs", "url": "https://app.clickup.com/t/869bwnc4a"},
    "869btrf5m": {"name": "[improvement][rt] Improve AIO brand detection", "url": "https://app.clickup.com/t/869btrf5m"},
    "869bt6nx8": {"name": "[feature request][writer] Review full keyword list before choosing topic", "url": "https://app.clickup.com/t/869bt6nx8"},
    "869bvwmhf": {"name": "[improvement][writer] Prevent keyword cannibalization in SEO Briefs", "url": "https://app.clickup.com/t/869bvwmhf"},
    "869bt962p": {"name": "[feature request][rt] Add notes directly on single keyword charts", "url": "https://app.clickup.com/t/869bt962p"},
    "869br664a": {"name": "[feature request][API] Supporting API access for Draft Campaigns", "url": "https://app.clickup.com/t/869br664a"},
    "869axgewg": {"name": "[improvement][research] Clicking + in KV navigates to adding kw instead of list", "url": "https://app.clickup.com/t/869axgewg"},
    "869b8etu5": {"name": "[improvement][rt] Discuss new chart designs for AIS", "url": "https://app.clickup.com/t/869b8etu5"},
    "869bcjdmv": {"name": "[feature request][looker] Implement YoY in looker reports", "url": "https://app.clickup.com/t/869bcjdmv"},
    "869b8cm0x": {"name": "[feature request][rt] Expose %clicks of individual SERP features", "url": "https://app.clickup.com/t/869b8cm0x"},
    "869bbjvrw": {"name": "[feature request][API] Expose CTR and blended SERP visibility", "url": "https://app.clickup.com/t/869bbjvrw"},
}


def update_cache_from_mcp_output(comments_by_task):
    """
    Update the cache file with fresh comment data.
    comments_by_task: dict of {task_id: {comments: [...], count: N}}
    """
    cache = {
        "last_updated": datetime.now().isoformat(),
        "tasks": {}
    }
    
    for task_id, data in comments_by_task.items():
        task_info = MONITORED_TASKS.get(task_id, {"name": "Unknown", "url": f"https://app.clickup.com/t/{task_id}"})
        comments = data.get("comments", [])
        
        cache["tasks"][task_id] = {
            "name": task_info["name"],
            "url": task_info["url"],
            "comments": []
        }
        
        for c in comments:
            cache["tasks"][task_id]["comments"].append({
                "id": c.get("id"),
                "date": c.get("date"),
                "user": c.get("user", {}).get("username", "Unknown"),
                "text": c.get("comment_text", "")[:300]
            })
    
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)
    
    print(f"✅ Cache updated: {sum(len(t['comments']) for t in cache['tasks'].values())} comments across {len(cache['tasks'])} tasks")
    return cache


def load_cache():
    """Load the comments cache file."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return None


def get_todays_comments(cache=None):
    """
    Filter cache for today's comments.
    Returns: {task_id: {"name": ..., "url": ..., "comments": [...]}}
    """
    if cache is None:
        cache = load_cache()
    if not cache:
        return {}
    
    now = datetime.now()
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_ms = int(today_midnight.timestamp() * 1000)
    
    result = {}
    for task_id, task_data in cache.get("tasks", {}).items():
        today_task_comments = []
        for c in task_data.get("comments", []):
            comment_ts = int(c.get("date", 0))
            if comment_ts >= today_start_ms:
                comment_time = datetime.fromtimestamp(comment_ts / 1000)
                today_task_comments.append({
                    "user": c["user"],
                    "time": comment_time.strftime("%H:%M"),
                    "text": c["text"],
                    "timestamp": comment_ts
                })
        
        if today_task_comments:
            today_task_comments.sort(key=lambda x: x["timestamp"])
            result[task_id] = {
                "name": task_data["name"],
                "url": task_data["url"],
                "comments": today_task_comments
            }
    
    return result


if __name__ == "__main__":
    cache = load_cache()
    if cache:
        print(f"Cache last updated: {cache.get('last_updated')}")
        today = get_todays_comments(cache)
        total = sum(len(t["comments"]) for t in today.values())
        print(f"Today's comments: {total} across {len(today)} tasks")
        for tid, tdata in today.items():
            print(f"\n  📋 {tdata['name']}")
            for c in tdata["comments"]:
                print(f"    {c['time']} - {c['user']}: {c['text'][:80]}...")
    else:
        print("No cache file found")
