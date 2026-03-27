import asyncio
import re
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

INTERCOM_API_TOKEN = os.getenv("INTERCOM_API_TOKEN")

def get_recent_items_from_intercom():
    if not INTERCOM_API_TOKEN:
        print("Error: INTERCOM_API_TOKEN is not set.")
        return []

    headers = {
        "Authorization": f"Bearer {INTERCOM_API_TOKEN}",
        "Accept": "application/json",
        "Intercom-Version": "2.11"
    }

    try:
        response = requests.get("https://api.intercom.io/conversations", headers=headers)
        response.raise_for_status()
        conversations = response.json().get("conversations", [])
        
        items_to_sync = []
        
        # Increase lookback to 14 days for testing
        current_time = int(time.time())
        lookback = current_time - (14 * 24 * 3600)

        print(f"Discovery: Checking {len(conversations)} recent conversations...")

        for conv in conversations:
            if conv.get("updated_at", 0) < lookback:
                continue

            conv_id = conv.get("id")
            # Fetch full conversation
            resp = requests.get(f"https://api.intercom.io/conversations/{conv_id}", headers=headers)
            if resp.status_code != 200:
                print(f"Failed to fetch {conv_id}")
                continue
            conv_detail = resp.json()

            source = conv_detail.get("source", {})
            subject = source.get("subject", "")
            body = source.get("body", "")
            
            full_text = f"{subject} {body}".lower()
            
            # Check conversation parts as well
            parts = conv_detail.get("conversation_parts", {}).get("conversation_parts", [])
            for part in parts:
                part_body = part.get("body", "")
                if part_body:
                    full_text += f" {part_body.lower()}"

            # Detection: mention usersnap and have a #3XXX or #4XXX ID
            usersnap_match = re.search(r"#([34]\d{3})", full_text)
            
            if "usersnap" in full_text or usersnap_match:
                print(f"Found match in conversation {conv_id}:")
                print(f"  Usersnap mentioned: {'usersnap' in full_text}")
                print(f"  ID Match: {usersnap_match.group(0) if usersnap_match else 'None'}")
                
                if usersnap_match:
                    usersnap_id = f"#{usersnap_match.group(1)}"
                    
                    clickup_match = re.search(r"https://app\.clickup\.com/t/[a-zA-Z0-9]+", full_text)
                    clickup_url = clickup_match.group(0) if clickup_match else ""

                    items_to_sync.append({
                        "usersnap_id": usersnap_id,
                        "clickup_url": clickup_url,
                        "conv_id": conv_id
                    })

        return items_to_sync

    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    items = get_recent_items_from_intercom()
    print(f"\nTotal items found: {len(items)}")
    for item in items:
        print(item)
