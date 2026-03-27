import asyncio
import os
import re
import requests
from playwright.async_api import async_playwright
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

INTERCOM_API_TOKEN = os.getenv("INTERCOM_API_TOKEN")
USERSNAP_PROJECT_URL = "https://app.usersnap.com/#/projects/31a2ba9a-4a79-42c7-9218-c8782d4a1435/list"
TARGET_ITEM_ID = "#3993"

def find_intercom_data(item_id, reporter, title):
    if not INTERCOM_API_TOKEN:
        print("⚠️ No Intercom Token found. Skipping lookup.")
        return None
        
    headers = {
        "Authorization": f"Bearer {INTERCOM_API_TOKEN}",
        "Accept": "application/json",
        "Intercom-Version": "2.11"
    }
    
    # 1. Search by Reporter Email (High Confidence)
    if reporter and "@" in reporter and reporter != "Unknown":
        print(f"    ℹ️ Search by Reporter: {reporter}")
        search_url = "https://api.intercom.io/conversations/search"
        query_payload = {
            "query": {
                "field": "source.author.email",
                "operator": "=",
                "value": reporter
            }
        }
        
        try:
            resp = requests.post(search_url, headers=headers, json=query_payload)
            if resp.status_code == 200:
                result_data = resp.json()
                conversations = result_data.get("conversations", [])
                print(f"    found {len(conversations)} comms by reporter.")
                
                for conv in conversations:
                    source = conv.get('source', {})
                    text_content = (source.get('subject', '') or '') + " " + (source.get('body', '') or '')
                    
                    if item_id in text_content:
                        print(f"    ✅ Found Match in Reporter History: {conv['id']}")
                        return extract_conversation_details(conv['id'], headers)
            else:
                 print(f"    ⚠️ Search API (Reporter) Error: {resp.text}")
        except Exception as e:
            print(f"    ⚠️ Search API Exception: {e}")

    # 2. Fallback: Search by ID in Subject
    print("    ℹ️ Fallback: Search by Subject match...")
    search_url = "https://api.intercom.io/conversations/search"
    query_payload = {
        "query": {
            "field": "source.subject",
            "operator": "~",
            "value": item_id
        }
    }
    try:
        resp = requests.post(search_url, headers=headers, json=query_payload)
        if resp.status_code == 200:
            result_data = resp.json()
            if result_data.get("total_count", 0) > 0:
                 conv = result_data["conversations"][0]
                 print(f"    ✅ Found Conversation via Subject Search: {conv['id']}")
                 return extract_conversation_details(conv['id'], headers)
    except:
        pass

    return None

def extract_conversation_details(conversation_id, headers):
    try:
        r = requests.get(f"https://api.intercom.io/conversations/{conversation_id}", headers=headers)
        if r.status_code != 200:
            return None
            
        detail = r.json()
        parts = detail.get('conversation_parts', {}).get('conversation_parts', [])
        source = detail.get('source', {})
        
        full_text = (source.get('subject') or "") + " " + (source.get('body') or "")
        for p in parts:
            full_text += " " + (p.get('body') or "")
            
        assignee = "Unassigned"
        teammates = detail.get('teammates', {}).get('teammates', [])
        if teammates:
            assignee = teammates[0].get('name')
        else:
            for p in reversed(parts):
                author = p.get('author', {})
                if author.get('type') == 'admin' and author.get('name'):
                    assignee = author.get('name')
                    break
        
        clickup_match = re.search(r"https://app\.clickup\.com/t/[a-zA-Z0-9]+", full_text)
        clickup_url = clickup_match.group(0) if clickup_match else None
        
        label = "Support" 
        tags = detail.get('tags', {}).get('tags', [])
        tag_names = [t.get('name', '').lower() for t in tags]
        
        if "bug" in tag_names or "bug" in full_text.lower():
            label = "Bug"
        elif "feature request" in tag_names or "feature" in full_text.lower():
            label = "Feature Request"
        
        return {
            "assignee": assignee,
            "clickup_url": clickup_url,
            "label": label,
            "priority": "None"
        }
    except Exception as e:
        print(f"    ⚠️ Error details extraction: {e}")
        return None

async def update_item_ui(page, item_id, data):
    if not data:
        return
        
    print(f"  📝 Updating {item_id}: {data}")
    
    # ASSIGNEE
    if data['assignee'] and data['assignee'] != "Unassigned":
        try:
            # Try multiple selectors for Assignee button
            assignee_btn = page.locator("button[data-testid='assignee-button'], button[aria-label*='Assignee'], div[class*='assignee'] button").first
            
            if await assignee_btn.is_visible():
                await assignee_btn.scroll_into_view_if_needed()
                curr_text = await assignee_btn.get_attribute("aria-label") or await assignee_btn.inner_text() or ""
                
                target_first = data['assignee'].split()[0].lower()
                
                if target_first not in curr_text.lower():
                    print(f"     > Opening Assignee Menu to find {data['assignee']}...")
                    await assignee_btn.click(force=True)
                    await page.wait_for_timeout(1000)
                    
                    # Update selector based on screenshot "Assign a team member"
                    search_inp = page.locator("input[placeholder*='Assign a team member'], input[placeholder*='Search user']").first
                    if await search_inp.is_visible():
                        await search_inp.fill(data['assignee'].split()[0])
                        await page.wait_for_timeout(1500)
                    else:
                         print("     ⚠️ Assignee search input not found (visible).")

                    # Debug: Print available options
                    options = page.locator("div[role='option'], div[role='menuitem']")
                    count = await options.count()
                    print(f"     Found {count} options in menu.")
                    
                    # Use looser matching for name
                    target_name = data['assignee'].split()[0] # e.g. Sulejman
                    option_to_click = page.locator(f"div[role='option']:has-text('{target_name}'), div[role='menuitem']:has-text('{target_name}')").first
                    
                    if await option_to_click.is_visible():
                        txt = await option_to_click.inner_text()
                        print(f"     > Selecting Option: {txt}")
                        await option_to_click.click(force=True)
                        print("    ✅ Assignee updated.")
                    else:
                        print(f"    ⚠️ Assignee {data['assignee']} not found in menu.")
                        await page.screenshot(path="debug_assignee_fail.png")
                        await page.keyboard.press("Escape")
            else:
                print("    ⚠️ Assignee button not found.")
        except Exception as e:
            print(f"    ⚠️ Failed to update assignee: {e}")
            await page.screenshot(path="debug_assignee_error.png")

    # CLICKUP NOTE
    if data['clickup_url']:
        try:
            comments = page.locator("div[class*='commentList']").first
            exists = False
            if await comments.is_visible():
                 txt = await comments.inner_text()
                 if data['clickup_url'] in txt: exists = True
            
            if exists:
                print("    ℹ️ ClickUp Note already exists.")
            else:
                # Try clicking "Add note" tab if present
                note_tab = page.locator("button:has-text('Add note')").first
                if await note_tab.is_visible():
                    await note_tab.click()
                    await page.wait_for_timeout(200)

                input_area = page.locator("textarea[placeholder*='Add a comment'], div[contenteditable='true']").first
                if await input_area.is_visible():
                    await input_area.click(force=True)
                    await page.wait_for_timeout(500)
                    
                    await input_area.fill(f"ClickUp Task: {data['clickup_url']}")
                    await page.wait_for_timeout(500)
                    # Submit button usually needed for notes
                    submit_btn = page.locator("button[type='submit']").last
                    if await submit_btn.is_visible():
                        await submit_btn.click()
                    else:
                        await page.keyboard.press("Meta+Enter")
                    print("    ✅ Note added.")
        except Exception as e:
            print(f"    ⚠️ Failed to add note: {e}")

    # LABEL
    if data['label']:
        try:
            label_name = data['label']
            # Try to verify if label exists first
            label_section = page.locator("div:has-text('LABELS') + div, div[class*='Labels']").first
            exists = False
            if await label_section.is_visible():
                 existing_text = await label_section.inner_text()
                 if label_name.lower() in existing_text.lower():
                     exists = True

            if exists:
                 print("    ℹ️ Label already exists.")
            else:
                 # Try multiple selectors for Label button
                 # Target using nearby heading "LABELS" to avoid clicking other things
                 add_label_btn = page.locator("div:has-text('LABELS') ~ button, button[data-testid='label-management']").first
                 
                 found_btn = False
                 if await add_label_btn.is_visible():
                     await add_label_btn.scroll_into_view_if_needed()
                     await add_label_btn.click(force=True)
                     found_btn = True
                 
                 if found_btn:
                     await page.wait_for_timeout(500)
                     # Specific selector for LABEL search input (avoid title input)
                     # Usually in a popover/tooltip
                     search_lbl = page.locator("div[role='tooltip'] input, div[class*='popover'] input, input[placeholder*='Find label']").first
                     
                     if await search_lbl.is_visible():
                         await search_lbl.fill(label_name)
                         await page.wait_for_timeout(1000)
                         
                         target_lbl = page.locator(f"div[role='option']:has-text('{label_name}')").first
                         if await target_lbl.is_visible():
                             await target_lbl.click(force=True)
                             print("    ✅ Label added.")
                         else:
                             print(f"    ⚠️ Label {label_name} not found in options.")
                             await page.screenshot(path="debug_label_fail.png")
                             await page.keyboard.press("Escape")
                     else:
                        print("    ⚠️ Label search input not found (or selector matched wrong input).")
                        await page.screenshot(path="debug_label_input_fail.png")
                        await page.keyboard.press("Escape")
                 else:
                    print("    ⚠️ Label button not found.")
        except Exception as e:
            print(f"    ⚠️ Failed to update label: {e}")

async def process_single_item():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile_fresh")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 720},
            args=[]
        )
        
        if context.pages:
            page = context.pages[0]
        else:
            page = await context.new_page()
        try:
            print(f"Navigating to Project List: {USERSNAP_PROJECT_URL}")
            # Use domcontentloaded instead of networkidle to avoid hanging on background requests
            await page.goto(USERSNAP_PROJECT_URL, timeout=60000, wait_until="domcontentloaded")
            # await page.wait_for_load_state("networkidle", timeout=60000) # Removed strictly waiting for network idle
            
            # Check for blocking banner
            try:
                banner_btn = page.locator("button:has-text('Not now')").first
                if await banner_btn.is_visible():
                    print("Dismissing 'Announcing Announcements' banner...")
                    await banner_btn.click()
                    await page.wait_for_timeout(1000)
            except: pass

            # SKIP AUTOMATED CLEARING - Wait for user intervention if list is empty
            print("Checking list state...")
            
            # Wait loop for list to populate
            max_wait_checks = 20
            for i in range(max_wait_checks):
                # Check directly for list items
                list_items = page.locator("li[class*='FeedbackItem'], div[class*='virtualized'] div[role='row']")
                count = await list_items.count()
                
                if count > 0:
                    print(f"✅ List populated with {count} items.")
                    break
                
                # Check for "No feedback" message
                empty_msg = page.locator("text=No feedback available")
                if await empty_msg.is_visible():
                     print(f"⚠️ List appears empty (Attempt {i+1}/{max_wait_checks}). Please CLEAR FILTERS manually in the browser!")
                else:
                     print(f"⏳ Waiting for list to load... ({i+1}/{max_wait_checks})")
                
                await page.wait_for_timeout(3000)
            
            
            print(f"Scanning for item {TARGET_ITEM_ID}...")
            await page.screenshot(path="debug_before_scroll.png")

            # Ensure we are on the list
            if "login" in page.url:
                print("⚠️  Login required. Please log in manually in the browser window!")
                await page.wait_for_timeout(60000)
            
            print(f"Scanning for item {TARGET_ITEM_ID}...")
            await page.screenshot(path="debug_before_scroll.png")
            
            # Scroll and find logic
            found_item = False
            # STRICT SELECTOR: Must be a list item (li) or have specific class
            item_locator = page.locator(f"li:has-text('{TARGET_ITEM_ID}'), div[class*='virtualized']:has-text('{TARGET_ITEM_ID}')").filter(has_text=TARGET_ITEM_ID).last
            
            # Identify list container for scrolling
            # Based on previous attempts, trying a few selectors or window scrolling
            list_container = page.locator("ul[class*='feedbackListContainer'], div[class*='virtualized-list'], div[class*='ReactVirtualized__Grid']").first
            
            max_scrolls = 20
            for i in range(max_scrolls):
                if await item_locator.is_visible():
                    print(f"✅ Found {TARGET_ITEM_ID} visible on screen.")
                    found_item = True
                    item_row = item_locator
                    break
                
                print(f"  Scrolling {i+1}/{max_scrolls}...")
                
                # Try scrolling the container if found, else page
                if await list_container.is_visible():
                    await list_container.evaluate("el => el.scrollTop = el.scrollTop + 500")
                else:
                    await page.mouse.wheel(0, 500)
                
                await page.wait_for_timeout(1000)
            
            if not found_item:
                print(f"⚠️ Item {TARGET_ITEM_ID} not found after scrolling.")
                # Final check with a broader search just in case
                item_row = page.locator(f"text={TARGET_ITEM_ID}").first
            
            if await item_row.is_visible():
                print(f"Found {TARGET_ITEM_ID}. Opening...")
                await item_row.click()
                
                # Cleanup UI (close filter dropdown if open)
                await page.keyboard.press("Escape")
                
                await page.wait_for_timeout(3000)
                await page.screenshot(path="debug_sidebar.png")
                
                # Scrape details
                sidebar = page.locator("div[class*='detailView'], div[class*='SplitView']").first
                if await sidebar.is_visible():
                     # Wait for Sidebar to load (Assignee button is a good proxy)
                     try:
                         print("Waiting for sidebar to fully load...")
                         await sidebar.locator("button[data-testid='assignee-button']").first.wait_for(state="visible", timeout=15000)
                         print("Sidebar loaded.")
                     except:
                         print("⚠️ Sidebar load timeout or buttons not found.")
                         await page.screenshot(path="debug_sidebar_loading.png")
                     
                     reporter = "Unknown"
                     possible_reporters = sidebar.locator("button, a").filter(has_text="@")
                     if await possible_reporters.count() > 0:
                         reporter = await possible_reporters.first.inner_text()
                     
                     title_input = sidebar.locator("input[name='title']").first
                     title = await title_input.input_value() if await title_input.count() > 0 else "No Title"

                     print(f"Details: Reporter={reporter}, Title={title}")
                     
                     # Intercom Lookup
                     intercom_data = find_intercom_data(TARGET_ITEM_ID, reporter, title)
                     
                     if intercom_data:
                         await update_item_ui(page, TARGET_ITEM_ID, intercom_data)
                     else:
                         print("❌ No matching Intercom data found.")
                else:
                    print("❌ Detail view did not open.")
                    await page.screenshot(path="debug_sidebar_fail.png")
            else:
                 print(f"❌ Item {TARGET_ITEM_ID} not found in list.")
                 
        except Exception as e:
            print(f"Global Error: {e}")
            await page.screenshot(path=f"debug_error_3993.png")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(process_single_item())
