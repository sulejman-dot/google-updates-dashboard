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
            assignee_btn = page.locator("button[data-testid='assignee-button']").first
            if await assignee_btn.is_visible():
                curr_text = await assignee_btn.get_attribute("aria-label") or ""
                
                # Check mismatch - FIRST NAME ONLY check
                target_first = data['assignee'].split()[0].lower()
                
                if target_first not in curr_text.lower():
                    print(f"     > Opening Assignee Menu to find {data['assignee']}...")
                    await assignee_btn.click(force=True)
                    await page.wait_for_timeout(1000)
                    
                    # Search by First Name only (Robustness)
                    search_inp = page.locator("input[placeholder*='Search user']").first
                    if await search_inp.is_visible():
                        await search_inp.fill(data['assignee'].split()[0])
                        await page.wait_for_timeout(1500)

                    # Pick first visible option
                    first_opt = page.locator("div[role='menu'] div[role='option']").first
                    if await first_opt.is_visible():
                        txt = await first_opt.inner_text()
                        print(f"     > Selecting Option: {txt}")
                        await first_opt.click(force=True)
                        print("    ✅ Assignee updated.")
                    else:
                        print(f"    ⚠️ Assignee {data['assignee']} not found in menu.")
                        await page.keyboard.press("Escape")
        except Exception as e:
            print(f"    ⚠️ Failed to update assignee: {e}")

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
                input_area = page.locator("textarea[placeholder*='Add a comment']").first
                if not await input_area.is_visible():
                    input_area = page.locator("div[class*='editableText']").first

                if await input_area.is_visible():
                    await input_area.click(force=True)
                    await page.wait_for_timeout(500)
                    
                    await input_area.fill(f"ClickUp Task: {data['clickup_url']}")
                    await page.wait_for_timeout(500)
                    await page.keyboard.press("Meta+Enter")
                    print("    ✅ Note added.")
        except Exception as e:
            print(f"    ⚠️ Failed to add note: {e}")

    # LABEL
    if data['label']:
        try:
            label_name = data['label']
            label_area = page.locator("div[class*='labelsWrapper']").first
            exists = False
            if await label_area.is_visible():
                 existing_text = await label_area.inner_text()
                 if label_name.lower() in existing_text.lower():
                     exists = True

            if exists:
                 print("    ℹ️ Label already exists.")
            else:
                 add_label_btn = page.locator("button[data-testid='label-management']").first
                 await add_label_btn.click(force=True)
                 await page.wait_for_timeout(500)
                 search_lbl = page.locator("input[placeholder*='Find label']").first
                 await search_lbl.type(label_name)
                 await page.wait_for_timeout(1000)
                 
                 target_lbl = page.locator(f"div[role='option']:has-text('{label_name}')").first
                 if await target_lbl.is_visible():
                     await target_lbl.click(force=True)
                     print("    ✅ Label added.")
                 else:
                     await page.keyboard.press("Escape")
        except Exception as e:
            print(f"    ⚠️ Failed to update label: {e}")


async def process_backlog():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=['--start-maximized']
        )
        
        page = await context.new_page()
        try:
            print(f"Navigating to Project List: {USERSNAP_PROJECT_URL}")
            await page.goto(USERSNAP_PROJECT_URL)
            await page.wait_for_timeout(5000)
            await page.mouse.click(10, 100) # Dismiss popups

            try:
                print("Clicking 'SEOmonitor feedback' project card...")
                project_card = page.locator("div, a").filter(has_text="SEOmonitor feedback").last
                await project_card.click()
                await page.wait_for_timeout(5000)
                await page.wait_for_load_state("networkidle")
                
                print("Checking URL for filters...")
                curr_url = page.url
                if "?" in curr_url or "number=" in curr_url:
                     print("  Reloading clean List URL...")
                     await page.goto(USERSNAP_PROJECT_URL, wait_until='networkidle')
                     await page.wait_for_timeout(3000)
                
                list_container = page.locator("ul[class*='feedbackListContainer']").first
                await list_container.wait_for(state="visible", timeout=10000)

            except Exception as e:
                print(f"⚠️ Navigation failed: {e}")
                return

            print("Scrolling to load all items...")
            last_count = 0
            while True:
                if await page.locator("div[class*='backdrop']").is_visible():
                     await page.keyboard.press("Escape")

                items_locators = list_container.locator("li div[class*='smallText']").filter(has_text=re.compile(r"^#\d+"))
                count = await items_locators.count()
                print(f"  > Found {count} items...")
                if count > last_count:
                    last_count = count
                    if count > 0: await items_locators.last.scroll_into_view_if_needed()
                    await list_container.evaluate("el => el.scrollTop = el.scrollHeight")
                    await page.wait_for_timeout(2000)
                else:
                    break
            
            print(f"Total visible items: {count}")
            
            processed_ids = set()
            
            for i in range(count):
                items_locators = list_container.locator("li div[class*='smallText']").filter(has_text=re.compile(r"^#\d+"))
                if i >= await items_locators.count(): break
                
                item_element = items_locators.nth(i)
                item_text = await item_element.inner_text()
                item_id = item_text.strip()
                
                if item_id in processed_ids: continue
                
                print(f"\nProcessing {item_id}...")
                
                try:
                    if await page.locator("div[class*='backdrop']").is_visible():
                        print("  Overlay detected. Pressing Escape...")
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(500)

                    item_row = list_container.locator(f"li:has-text('{item_id}')").first
                    await item_row.scroll_into_view_if_needed()
                    
                    await item_row.click(force=True)
                    await page.wait_for_timeout(2000)
                    
                    if await page.locator("div[class*='detailView']").is_visible():
                        sidebar = page.locator("div[class*='detailView']")
                        reporter = "Unknown"
                        
                        try:
                            await sidebar.locator("input[name='title']").first.wait_for(timeout=3000)
                        except:
                            print("  ⚠️ Sidebar Slow Load.")
                        
                        possible_reporters = sidebar.locator("button, a").filter(has_text="@")
                        if await possible_reporters.count() > 0:
                            reporter = await possible_reporters.first.inner_text()
                        
                        title_input = sidebar.locator("input[name='title']").first
                        title = await title_input.input_value() if await title_input.count() > 0 else "No Title"
                        
                        print(f"  > Item: {item_id}")
                        print(f"  > Reporter: {reporter}")
                        print(f"  > Title: {title[:50]}...")
                        
                        intercom_data = find_intercom_data(item_id, reporter, title)
                        
                        if intercom_data:
                            await update_item_ui(page, item_id, intercom_data)
                            
                        processed_ids.add(item_id)
                    else:
                        print("  ❌ Sidebar did not open.")
                        
                except Exception as e:
                    print(f"  ❌ Error processing item: {e}")

        except Exception as e:
            print(f"Global Error: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(process_backlog())
