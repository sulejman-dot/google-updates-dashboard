import os
import requests
import re
from dotenv import load_dotenv

load_dotenv()

INTERCOM_API_TOKEN = os.getenv("INTERCOM_API_TOKEN")
CONV_ID = "215472832138717"

def analyze_conversation():
    headers = {
        "Authorization": f"Bearer {INTERCOM_API_TOKEN}",
        "Accept": "application/json",
        "Intercom-Version": "2.11"
    }
    
    print(f"Fetching Conversation {CONV_ID}...")
    resp = requests.get(f"https://api.intercom.io/conversations/{CONV_ID}", headers=headers)
    
    if resp.status_code != 200:
        print(f"Error: {resp.text}")
        return
        
    data = resp.json()
    
    # Extract Parts
    parts = data.get('conversation_parts', {}).get('conversation_parts', [])
    source = data.get('source', {})
    subject = source.get('subject', '') or ''
    body = source.get('body', '') or ''
    
    full_text = f"{subject} {body}".lower()
    for p in parts:
        full_text += " " + (p.get('body') or "").lower()
        
    # 1. Assignee (Last Admin)
    # Default to Sulejman if unassigned, or find last admin
    assignee = "Unassigned"
    for p in reversed(parts):
        author = p.get('author', {})
        if author.get('type') == 'admin':
            assignee = author.get('name')
            break
            
    # 2. ClickUp URL
    clickup_match = re.search(r"https://app\.clickup\.com/t/[a-zA-Z0-9]+", full_text)
    clickup_url = clickup_match.group(0) if clickup_match else None
    
    # 3. Tags/Labels
    tags = data.get("tags", {}).get("tags", [])
    tag_names = [t.get("name") for t in tags]
    
    # 4. Classification Logic
    labels_to_add = []
    priority = "None"
    
    # Bug vs Feature vs Support
    if clickup_url:
        if "product" in clickup_url.lower():
            labels_to_add.append("Feature")
        else:
            labels_to_add.append("Bug")
    elif "bug" in full_text:
        labels_to_add.append("Bug")
    else:
        labels_to_add.append("Support")
        
    # Priority
    if any(k in full_text for k in ["urgent", "critical", "asap"]):
        priority = "High"
    if "TierA" in tag_names:
        priority = "High"
        
    print("\n--- Analysis Results ---")
    print(f"Conversation ID: {CONV_ID}")
    print(f"Assignee: {assignee}")
    print(f"ClickUp URL: {clickup_url}")
    print(f"Existing Tags: {tag_names}")
    print(f"Proposed Labels: {labels_to_add}")
    print(f"Proposed Priority: {priority}")
    print("------------------------")

if __name__ == "__main__":
    analyze_conversation()
