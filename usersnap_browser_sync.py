import asyncio
import re
import os
import time
import json
import requests
import argparse
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load configuration from .env file
load_dotenv()

# --- Configuration ---
# 1. Provide your Intercom API Token
INTERCOM_API_TOKEN = os.getenv("INTERCOM_API_TOKEN", "YOUR_TOKEN_HERE")
# 2. Usersnap Project Base URL
USERSNAP_BASE_URL = "https://app.usersnap.com/#/projects/31a2ba9a-4a79-42c7-9218-c8782d4a1435/list"
# 3. Synced IDs file to avoid duplicates
SYNCED_IDS_FILE = "synced_ids.txt"
# 4. Polling Interval (seconds)
POLLING_INTERVAL = 600 # 10 minutes

def load_synced_ids():
    if os.path.exists(SYNCED_IDS_FILE):
        with open(SYNCED_IDS_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_synced_id(usersnap_id):
    with open(SYNCED_IDS_FILE, "a") as f:
        f.write(f"{usersnap_id}\n")

def get_recent_items_from_intercom():
    """
    Searches for recent Intercom conversations containing 'Usersnap'.
    """
    if INTERCOM_API_TOKEN == "YOUR_TOKEN_HERE":
        print("Error: INTERCOM_API_TOKEN is not set. Please update the configuration.")
        return []

    headers = {
        "Authorization": f"Bearer {INTERCOM_API_TOKEN}",
        "Accept": "application/json",
        "Intercom-Version": "2.11"
    }

    try:
        # 1. Get recent conversations (proven method)
        response = requests.get("https://api.intercom.io/conversations", headers=headers)
        response.raise_for_status()
        conversations = response.json().get("conversations", [])
        
        items_to_sync = []
        synced_ids = load_synced_ids()
        
        # Filter for items updated in the last 48 hours for buffer
        current_time = int(time.time())
        two_days_ago = current_time - (48 * 3600)

        print(f"Discovery: Checking {len(conversations)} recent conversations...")

        for conv in conversations:
            updated_at = conv.get("updated_at", 0)
            if updated_at < two_days_ago:
                continue

            conv_id = conv.get("id")
            
            # Fetch full conversation
            resp = requests.get(f"https://api.intercom.io/conversations/{conv_id}", headers=headers)
            if resp.status_code != 200:
                continue
            conv_detail = resp.json()
            
            source = conv_detail.get("source", {})
            subject = source.get("subject", "")
            body = source.get("body", "")
            
            full_text = f"{subject} {body}".lower()
            parts = conv_detail.get("conversation_parts", {}).get("conversation_parts", [])
            
            # Combine all text for detection
            for part in parts:
                part_body = part.get("body", "")
                if part_body:
                    full_text += f" {part_body.lower()}"
            
            # Discovery: Must mention usersnap or have a direct link or have a #3XXX/#4XXX ID
            direct_link_match = re.search(r"https://app\.usersnap\.com/l/feedback/([a-z0-9-]+)", full_text)
            usersnap_id_match = re.search(r"#([34]\d{3})", full_text)
            
            if not (direct_link_match or "usersnap" in full_text or usersnap_id_match):
                continue
                
            usersnap_id = f"#{usersnap_id_match.group(1)}" if usersnap_id_match else "Linked Item"
            direct_url = direct_link_match.group(0) if direct_link_match else ""

            if usersnap_id in synced_ids and not direct_url:
                continue

            # Look for ClickUp URL - STRICT MATCH for app.clickup.com/t/
            clickup_match = re.search(r"https://app\.clickup\.com/t/[a-zA-Z0-9]+", full_text)
            clickup_url = clickup_match.group(0) if clickup_match else ""

            # Assignee mapping: find the first actual admin who replied
            assignee = "Sulejman" # Default
            for part in reversed(parts):
                author = part.get("author", {})
                if author.get("type") == "admin" and author.get("name"):
                    assignee = author.get("name")
                    break
            
            # Labels (from Intercom tags)
            raw_tags = conv_detail.get("tags", {})
            usersnap_identifier = f"#{usersnap_id_match.group(1)}" if usersnap_id_match else "Linked Item"
            if direct_link_match or "usersnap" in full_text or usersnap_id_match:
                 print(f"DEBUG: Found {usersnap_identifier} in Conv {conv_id} | Tags: {[t.get('name') for t in raw_tags.get('tags', [])]}")
            
            
            # Labels Logic (Based on ClickUp URL)
            # - No ClickUp URL -> Support
            # - ClickUp URL present -> Bug
            # - ClickUp URL with 'product' -> Feature
            labels = []
            if not clickup_url:
                labels.append("Support")
            else:
                if "product" in clickup_url.lower():
                    labels.append("Feature")
                else:
                    labels.append("Bug")

            # Priority (Based on Intercom labels or text)
            priority = "None"
            tags_lower = [l.lower() for l in labels]
            high_priority_keywords = ["bug", "feature", "improvement", "request"]
            if any(kw in tags_lower for kw in high_priority_keywords) or "urgent" in full_text:
                priority = "High"

            items_to_sync.append({
                "usersnap_id": usersnap_id,
                "direct_url": direct_url,
                "assignee": assignee,
                "priority": priority,
                "labels": labels,
                "clickup_url": clickup_url
            })

        # Deduplicate items by usersnap_id
        unique_map = {}
        for item in items_to_sync:
            uid = item['usersnap_id']
            if uid not in unique_map:
                unique_map[uid] = item
            else:
                # If existing doesn't have direct_url but this one does, update it
                if item['direct_url'] and not unique_map[uid]['direct_url']:
                    unique_map[uid] = item
        
        return list(unique_map.values())

    except Exception as e:
        print(f"Error fetching from Intercom: {e}")
        return []

async def sync_to_usersnap(data, context, dry_run=False):
    """
    Performs the UI automation for a single item using an existing context.
    """
    page = await context.new_page()
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        target_id = data.get('usersnap_id') or data.get('direct_url')
        print(f"[{timestamp}] --- Processing {target_id} ---")
        
        if data.get('direct_url'):
            print(f"Navigating directly to {data['direct_url']}...")
            await page.goto(data['direct_url'])
            # Wait for content or a redirect to the list view
            await page.wait_for_timeout(5000) 
        else:
            await page.goto(USERSNAP_BASE_URL)

        # Wait for the dashboard or item view
        # Wait for the dashboard or item view
        try:
            # Check for content OR login fields
            element = await page.wait_for_selector('div[class*="Details"], input[placeholder*="filter"], div[class*="Feedback"], input[name="email"], input[type="password"]', timeout=30000)
            
            # Check if we are on the login page
            if await page.locator('input[name="email"], input[type="password"]').count() > 0 or "login" in page.url:
                print("⚠️  Login required. Pausing 60s for manual login... Please log in in the browser window!")
                await page.wait_for_timeout(60000)
                
                # Check again if we advanced
                if "login" in page.url and await page.locator('input[name="email"]').count() > 0:
                     print("❌ Still on login page after wait. Skipping.")
                     return False
                else:
                     print("✅ Login assumed successful (or URL changed). Continuing...")
                     # Wait a bit more for dashboard to fully load
                     await page.wait_for_timeout(5000)

            # Re-verify dashboard element specifically if we want to be sure
            # await page.wait_for_selector('div[class*="Details"], input[placeholder*="filter"]', timeout=10000)
            
        except Exception as e:
            print(f"Dashboard/Item not loaded for {target_id}. Error: {e} Skipping.")
            await page.screenshot(path="debug_init_fail.png")
            return False

        # 1. Search if not already on the item page
        # Note: Checks if current URL has a UUID-like pattern or 'feedback'
        # Also trust if we just navigated to a direct URL
        is_on_item = re.search(r"/feedback/[a-z0-9-]{36}", page.url) or (data.get('direct_url') and data['direct_url'] in page.url)
        
        if not is_on_item:
            print(f"Current URL: {page.url} does not match item pattern. Searching for {data['usersnap_id']}...")
            search_input = page.locator('input[placeholder*="filter"]')
            await search_input.click()
            
            # Layer 1: Try to click "x" buttons (chips)
            # Strategy: Look for SVGs that are siblings or children of the search container
            # The 'editorMenuItem' class was seen in CSS for the tooltip
            try:
                # Assuming chips are siblings to the input or in the same container
                # We target the parent of the input
                search_container = search_input.locator("..")
                # Look for clickable SVGs (excluding the search icon itself)
                # We can try to click any SVG that is NOT the search icon (often left-most)
                # But safer to look for "Delete" or "Clear" clues if possible
                
                # Try specific class from investigation
                delete_btns = search_container.locator("div[class*='editorMenuItem'] svg, svg[class*='close'], svg[data-icon='times']")
                count = await delete_btns.count()
                for i in range(count):
                    try:
                        if await delete_btns.nth(i).is_visible():
                            await delete_btns.nth(i).click()
                            await page.wait_for_timeout(200)
                    except:
                        pass
            except Exception as e:
                print(f"Debug: Failed to click delete buttons: {e}")

            # Layer 2: Select all and delete (for text)
            await page.keyboard.press("Meta+A")
            await page.keyboard.press("Backspace")
            
            # Layer 3: Backspace loop for remaining chips
            for _ in range(10):
                await page.keyboard.press("Backspace")
                await page.wait_for_timeout(50)
                
            await search_input.fill("") 
            await search_input.fill(data['usersnap_id'])
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3000)

            # Open the first result - check if it exists first
            result = page.locator(f"text={data['usersnap_id']}").first
            try:
                await result.wait_for(state="visible", timeout=10000)
                print(f"Opening result for {data['usersnap_id']}...")
                await result.scroll_into_view_if_needed()
                await result.dispatch_event("click")
                await page.wait_for_timeout(3000)
            except:
                print(f"❌ Could not find search result for {data['usersnap_id']}. Skipping.")
                await page.screenshot(path="debug_search_fail.png")
                return False

        if dry_run:
            print(f"DRY RUN: Would update {target_id} with Assignee: {data['assignee']}, Priority: {data['priority']}, Labels: {data['labels']}, Note: {data['clickup_url']}")
            await page.wait_for_timeout(2000)
            return True

        # 3. Update Assignee
        try:
            # data-testid='assignee-button' is reliable
            assignee_btn = page.locator("button[data-testid='assignee-button']").first
            if await assignee_btn.is_visible():
                await assignee_btn.scroll_into_view_if_needed(timeout=5000)
                current_assignee = await assignee_btn.get_attribute("aria-label") or ""
                # Check if current assignee contains the desired name
                if data['assignee'] not in current_assignee:
                    await assignee_btn.click(force=True)
                    # Select from dropdown
                    await page.locator(f"div[role='menu'] div:has-text('{data['assignee']}'), div[role='listbox'] div:has-text('{data['assignee']}')").first.click(force=True)
                    print(f"Assignee set to {data['assignee']}")
                else:
                     print(f"Assignee already match: {data['assignee']}")
        except Exception as e:
            print(f"Note: Could not set assignee: {e}")

        # 4. Update Priority
        try:
            if data['priority'] == "High":
                # Start with aria-label which is most distinct
                priority_btn = page.locator("button[aria-label='Priority'], button[aria-label='None'], button[aria-label='Low'], button[aria-label='Medium'], button[aria-label='High']").first
                
                # Fallback
                if not await priority_btn.count():
                     priority_btn = page.locator("button:has-text('Priority')").first

                if await priority_btn.is_visible():
                    await priority_btn.scroll_into_view_if_needed(timeout=5000)
                    current_prio = await priority_btn.get_attribute("aria-label") or await priority_btn.inner_text()
                    
                    if "High" not in current_prio:
                        await priority_btn.click(force=True)
                        # Explicitly wait for the menu
                        high_option = page.locator("div[role='menu'] div:has-text('High'), div[role='listbox'] div:has-text('High')").first
                        await high_option.wait_for(state="visible", timeout=3000)
                        await high_option.click(force=True)
                        print("Priority set to High")
                    else:
                        print("Priority is already High.")
        except Exception as e:
            print(f"Note: Could not set priority: {e}")

        # 5. Add ClickUp URL
        if data['clickup_url']:
            try:
                # Check if note already exists (narrow scope)
                notes_text = await page.locator("div[class*='CommentList'], div[class*='Timeline']").inner_text()
                if data['clickup_url'] in notes_text:
                    print("Note already exists in Usersnap. Skipping.")
                else:
                    # Click "Add note" tab
                    add_note_tab = page.locator("button:has-text('Add note')").filter(has_not=page.locator("[type='submit']")).first
                    await add_note_tab.scroll_into_view_if_needed(timeout=5000)
                    await add_note_tab.click(force=True)
                    
                    # Wait for ProseMirror editor
                    editor = page.locator(".ProseMirror").first
                    await editor.wait_for(state="visible", timeout=5000)
                    await editor.click() 
                    await editor.type(data['clickup_url'])
                    
                    # Click blue "Add note" submit button
                    submit_btn = page.locator("button[type='submit']").filter(has_text="Add note").first
                    await submit_btn.click(force=True)
                    print("Note successfully added.")
            except Exception as e:
                print(f"Note sync failed: {str(e)}")

        # 6. Set Status to Done
        try:
            status_btn = page.locator("button[aria-label='Status'], button:has-text('Open'), button:has-text('In Progress')").first
            if await status_btn.is_visible():
                 await status_btn.scroll_into_view_if_needed(timeout=5000)
                 current_status = await status_btn.get_attribute("aria-label") or await status_btn.inner_text()
                 if "Done" not in current_status:
                    await status_btn.click(force=True)
                    done_option = page.locator("div[role='menu'] div:has-text('Done'), div[role='listbox'] div:has-text('Done')").first
                    await done_option.click(force=True)
                    print("Status set to Done")
                 else:
                    print("Status already Done")
        except Exception as e:
            print(f"Note: Could not set status: {e}")

        # 7. Add Labels
        if data['labels']:
            try:
                # data-testid='label-management' is reliable
                add_label_btn = page.locator("button[data-testid='label-management']").first
                
                if await add_label_btn.is_visible():
                    await add_label_btn.click()
                else:
                     # fallback
                     labels_header = page.locator("div:has-text('Labels')").first
                     await labels_header.click()
                
                # Check for input - handle timeout gracefully
                try: 
                    label_input = page.locator("input[placeholder*='Find or create label'], input[placeholder*='Add filter']").first
                    await label_input.wait_for(state="visible", timeout=3000)
                    
                    for label in data['labels']:
                        await label_input.fill(label)
                        await page.wait_for_timeout(500)
                        await page.keyboard.press("Enter")
                        print(f"Added label: {label}")
                except Exception:
                     print("Label input not found or timed out.")
                finally:
                    # Closing label picker is CRITICAL to avoid blocking other elements
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(500)
                
            except Exception as e:
                print(f"Note: Could not sync labels: {e}")

        if data['usersnap_id'] != "Linked Item":
            save_synced_id(data['usersnap_id'])
        print(f"✅ Sync complete for {target_id}")
        return True

    except Exception as e:
        print(f"Error syncing {target_id}: {e}")
        return False
    finally:
        await page.close()

async def run_sync_cycle(dry_run=False):
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            slow_mo=500,
            viewport=None,
            args=['--start-maximized']
        )

        try:
            # Short verification that we're mostly okay
            page = await context.new_page()
            await page.goto("https://app.usersnap.com/")
            await page.wait_for_timeout(3000)
            if "login" in page.url:
                print("⚠️  Warning: Playwright session might be expired. Manual login may be needed.")
            await page.close()

            items = get_recent_items_from_intercom()
            if not items:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No new items found in Intercom.")
            else:
                print(f"Found {len(items)} items to sync.")
                for item in items:
                    success = await sync_to_usersnap(item, context, dry_run=dry_run)
                    if not success:
                        print(f"Failed to sync {item.get('usersnap_id')}. Skipping to next item.")
                        continue
        finally:
            await context.close()

async def main():
    parser = argparse.ArgumentParser(description="Usersnap-Intercom Browser Synchronization Service")
    parser.add_argument("--dry-run", action="store_true", help="Simulate updates without making changes")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    mode_text = "DRY RUN MODE" if args.dry_run else "LIVE MODE"
    print(f"🚀 Starting Usersnap-Intercom Polling Service ({mode_text})...")
    
    while True:
        await run_sync_cycle(dry_run=args.dry_run)
        if args.once:
            break
        print(f"Waiting {POLLING_INTERVAL} seconds for next check...")
        await asyncio.sleep(POLLING_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
