import os
import requests
from dotenv import load_dotenv

load_dotenv()

INTERCOM_API_TOKEN = os.getenv("INTERCOM_API_TOKEN")

def search_for_item(item_id):
    headers = {
        "Authorization": f"Bearer {INTERCOM_API_TOKEN}",
        "Accept": "application/json",
        "Intercom-Version": "2.11"
    }
    
    print(f"Fetching conversations via pagination to find {item_id}...")
    
    url = "https://api.intercom.io/conversations"
    params = {"per_page": 20}
    
    found = False
    pages_checked = 0
    max_pages = 5
    
    while url and pages_checked < max_pages:
        print(f"Checking page {pages_checked + 1}...")
        resp = requests.get(url, headers=headers, params=params if pages_checked == 0 else {})
        if resp.status_code != 200:
            print(f"Error fetching list: {resp.text}")
            break
            
        data = resp.json()
        conversations = data.get("conversations", [])
        
        for conv in conversations:
            # Check snippet first
            source = conv.get('source', {})
            subject = source.get('subject', '') or ''
            body = source.get('body', '') or ''
            
            # Basic check in snippet
            snippet_text = f"{subject} {body}".lower()
            
            if item_id.lower() in snippet_text:
                print(f"\n✅ FOUND MATCH in List Snippet! Conv {conv['id']}")
                # NOW fetch full details to be sure and get assignee/clickup
                r = requests.get(f"https://api.intercom.io/conversations/{conv['id']}", headers=headers)
                if r.status_code == 200:
                    conv_detail = r.json()
                    parts = conv_detail.get('conversation_parts', {}).get('conversation_parts', [])
                    full_text = snippet_text
                    for p in parts:
                        full_text += " " + (p.get('body') or "").lower()
                        
                    print(f"Link: https://app.intercom.com/a/inbox/_/inbox/conversation/{conv['id']}")
                    
                    assignee = "Unassigned"
                    for p in reversed(parts):
                        author = p.get('author', {})
                        if author.get('type') == 'admin' and author.get('name'):
                            assignee = author.get('name')
                            break
                    print(f"Assignee: {assignee}")
                    
                    import re
                    clickup = re.search(r"https://app\.clickup\.com/t/[a-zA-Z0-9]+", full_text)
                    clickup_url = clickup.group(0) if clickup else 'None'
                    print(f"ClickUp URL: {clickup_url}")
                    
                    is_bug = "bug" in full_text
                    has_clickup = clickup_url != 'None'
                    if has_clickup: print("Status Idea: Bug (has ClickUp link)")
                    elif is_bug: print("Status Idea: Bug (mentioned in text)")
                    else: print("Status Idea: Support/Feedback")
                    
                    found = True
                    break
        
        if found:
            break
            
        pages_checked += 1
        paging = data.get("pages", {})
        if "next" in paging and "starting_after" in paging["next"]:
            starting_after = paging["next"]["starting_after"]
            # Important: Restart loop with same URL but different params
            url = "https://api.intercom.io/conversations"
            params = {"per_page": 20, "starting_after": starting_after}
        else:
            break
            
    if not found:
        print(f"❌ Could not find {item_id} in recent conversations.")

if __name__ == "__main__":
    search_for_item("#4017")
