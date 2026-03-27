import asyncio
import os
from playwright.async_api import async_playwright

# Configuration
USERSNAP_PROJECT_URL = "https://app.usersnap.com/#/projects/31a2ba9a-4a79-42c7-9218-c8782d4a1435/list" # Main list view
ASSIGNEE = "Sulejman"
PRIORITY = "High"
LABEL = "test-automation"
NOTE = "Automated test note: Verifying script logic."

async def find_and_update_latest():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            slow_mo=1000, # Slower for visibility
            viewport=None,
            args=['--start-maximized']
        )

        page = await context.new_page()
        try:
            print(f"Navigating to Project Dashboard: {USERSNAP_PROJECT_URL}")
            await page.goto(USERSNAP_PROJECT_URL)
            
            # 1. Login Check
            try:
                # Quick check if redirected to login
                await page.wait_for_timeout(3000)
                if "login" in page.url or await page.locator("input[type='password']").count() > 0:
                    print("⚠️  Login Page Detected! Please log in manually within 60 seconds...")
                    await page.wait_for_timeout(60000)
                    if "login" in page.url:
                        print("❌ Still on login page. Aborting.")
                        return
            except:
                pass

            # 2. Wait for List View
            print("Waiting for list view...")
            # Found: <ul class="feedbackListContainer-...">
            await page.wait_for_selector("ul[class*='feedbackListContainer']", timeout=20000)

            # 3. Find first "Open" item
            print("Scanning items...")
            
            # Strategy: Get all 'li' elements in the feedback list
            items = page.locator("ul[class*='feedbackListContainer'] > li").all()
            items = await items
            print(f"Found {len(items)} items in the list.")
            
            target_item = None
            
            for item in items:
                # Check for "Done" class or style
                # In dump: class="... container_done-..." or title class has "title_done"
                class_attr = await item.get_attribute("class") or ""
                
                # Use .first to avoid strict mode error if multiple title-like divs exist
                title_el = item.locator("div[class*='title']").first 
                title_class = await title_el.get_attribute("class") or "" if await title_el.count() > 0 else ""
                
                if "done" in class_attr.lower() or "done" in title_class.lower():
                    # print("Skipping done item")
                    continue
                
                # Double check text just in case
                text = await item.inner_text()
                if "Done" in text and "Status" in text: # Sometimes status text is visible
                    continue

                target_item = item
                print(f"✅ Found candidate item: {text.splitlines()[0][:50]}...")
                break
            
            if not target_item:
                print("❌ No open items found in the current view.")
                # We might be on a view with only done items?
                return

            # 4. Open the item
            print("Opening item...")
            # Click the contentWrapper or just the item
            await target_item.click()
            
            # 5. Wait for Detail View
            # Found: <main class="feedback-...">
            # Or <div class="detailView-...">
            await page.wait_for_selector('main[class*="feedback"], div[class*="detailView"]', timeout=20000)
            print("Item opened.")
            await page.wait_for_timeout(2000)

            # --- UPDATE LOGIC (Copied/Adapted from main script) ---

            # A. Update Assignee
            try:
                print(f"Setting assignee to {ASSIGNEE}...")
                # Button often has aria-label="Assignee" or "Unassigned" or the name of current assignee
                # From dump: <button ... aria-label="Sulejman Lekovic" data-testid="assignee-button">
                assignee_btn = page.locator("button[data-testid='assignee-button']").first
                if await assignee_btn.is_visible():
                    await assignee_btn.scroll_into_view_if_needed(timeout=5000)
                    aria_label = await assignee_btn.get_attribute("aria-label") or ""
                    
                    if ASSIGNEE not in aria_label:
                        await assignee_btn.click(force=True)
                        # Wait for dropdown
                        await page.locator(f"div[role='menu'] div:has-text('{ASSIGNEE}'), div[role='listbox'] div:has-text('{ASSIGNEE}')").first.click(force=True)
                        print(f"Assignee set to {ASSIGNEE}")
                    else:
                        print(f"Assignee already set to {ASSIGNEE}")
                else:
                    print("Assignee button not found (data-testid='assignee-button').")
            except Exception as e:
                print(f"Assignee step warning: {e}")

            # B. Update Priority
            try:
                print(f"Setting Priority to {PRIORITY}...")
                # From dump: <button ... aria-label="High"><div class="label...">High</div>
                # It seems buttons are identified by aria-label often
                priority_btn = page.locator("button[aria-label='Priority'], button[aria-label='None'], button[aria-label='Low'], button[aria-label='Medium'], button[aria-label='High']").first
                
                # If specific locator fails, try finding button containing "Priority" text if unlabeled
                if not await priority_btn.count():
                     priority_btn = page.locator("button:has-text('Priority')").first

                if await priority_btn.is_visible():
                    current_prio = await priority_btn.get_attribute("aria-label") or await priority_btn.inner_text()
                    if PRIORITY not in current_prio:
                        await priority_btn.click(force=True)
                        # Wait for dropdown
                        high_option = page.locator(f"div[role='menu'] div:has-text('{PRIORITY}'), div[role='listbox'] div:has-text('{PRIORITY}')").first
                        await high_option.wait_for(state="visible", timeout=3000)
                        await high_option.click(force=True)
                        print(f"Priority updated to {PRIORITY}")
                    else:
                        print(f"Priority is already {PRIORITY}")
            except Exception as e:
                 print(f"Priority step warning: {e}")

            # C. Add Label
            try:
                print(f"Adding label '{LABEL}'...")
                # Look for "Add label" button or data-testid="label-management"
                # From dump: <button ... data-testid="label-management">
                add_label_btn = page.locator("button[data-testid='label-management']").first
                
                if await add_label_btn.is_visible():
                     await add_label_btn.click()
                
                # Input
                label_input = page.locator("input[placeholder*='Find or create']").first
                if await label_input.is_visible():
                    await label_input.fill(LABEL)
                    await page.wait_for_timeout(1000)
                    await page.keyboard.press("Enter")
                    await page.keyboard.press("Escape")
                    print(f"Label '{LABEL}' added.")
            except Exception as e:
                print(f"Label step warning: {e}")

            # D. Add Note
            try:
                print("Adding test note...")
                # Tab "Add note"
                add_note_tab = page.locator("button:has-text('Add note')").first
                if await add_note_tab.is_visible():
                    await add_note_tab.click()
                    
                    # ProseMirror
                    editor = page.locator(".ProseMirror").first
                    await editor.wait_for(state="visible")
                    await editor.click()
                    await editor.type(NOTE)
                    
                    submit_btn = page.locator("button[type='submit']").filter(has_text="Add note").first
                    await submit_btn.click()
                    print("Note added.")
            except Exception as e:
                print(f"Note step warning: {e}")

            print("✅ Live test sequence complete.")
            await page.wait_for_timeout(5000)

        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            await page.screenshot(path="debug_live_test_error.png")
            print("Saved debug_live_test_error.png")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(find_and_update_latest())
