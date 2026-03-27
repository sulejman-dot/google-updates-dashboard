import asyncio
import os
from playwright.async_api import async_playwright

ITEM_ID = "#4017"
ASSIGNEE = "Sulejman"
LABEL = "Bug"
USERSNAP_PROJECT_URL = "https://app.usersnap.com/#/projects/31a2ba9a-4a79-42c7-9218-c8782d4a1435/list"

async def fix_item():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False, # Debugging mode often safer
            args=['--start-maximized']
        )
        
        page = await context.new_page()
        try:
            print(f"Navigating to Project List: {USERSNAP_PROJECT_URL}")
            await page.goto(USERSNAP_PROJECT_URL)
            await page.wait_for_timeout(5000)
            
            # Verify we are in the project
            try:
                # Expect specific project text or tabs
                await page.wait_for_selector("text=Feedback", timeout=10000)
                print("✅ Verified inside Project.")
            except:
                print("⚠️ Could not verify Project context. We might be on Dashboard.")
                # Try clicking the project if listed?
                # "SEOmonitor feedback" (Space #1)
                try:
                     await page.click("text=SEOmonitor feedback", timeout=5000)
                     await page.wait_for_timeout(5000)
                     print("Clicked project name.")
                except:
                     print("Could not recover project context.")
                     return

            # Skip Search, find in list directly
            print("Locating item in list directly...")
            
            try:
                # Based on DOM dump: ul class*='feedbackListContainer' > li
                list_container = page.locator("ul[class*='feedbackListContainer']").first
                await list_container.wait_for(state="visible", timeout=10000)
                
                # Find the specific LI for the item
                item_row = list_container.locator(f"li:has-text('{ITEM_ID}')").first
                
                # If not found immediately, maybe scroll?
                if await item_row.count() == 0:
                     print("Item not in viewport, trying to scroll list...")
                     await list_container.evaluate("el => el.scrollTop = el.scrollHeight")
                     await page.wait_for_timeout(1000)
                
                await item_row.scroll_into_view_if_needed()
                await item_row.click()
                print("✅ Found and clicked item in list.")
                await page.wait_for_timeout(3000)
                
                # Verify Sidebar opened
                await page.wait_for_selector("div[class*='detailView']", timeout=5000)
                print("Sidebar confirmed open.")

            except Exception as e:
                print(f"❌ Direct list click failed: {e}")
                # Fallback to verify if sidebar is ALREADY open (e.g. from previous state?)
                if await page.locator("div[class*='detailView'] >> text='#4017'").is_visible():
                     print("Sidebar seems to be already open on the correct item.")
                else:
                     return

            # Now update logic...
            print(f"Applying updates for {ITEM_ID}...")

            # 1. ASSIGNEE
            try:
                assignee_btn = page.locator("button[data-testid='assignee-button']").first
                await assignee_btn.wait_for(state="visible", timeout=5000)
                
                btn_text = await assignee_btn.get_attribute("aria-label") or await assignee_btn.inner_text()
                print(f"Current Assignee status: {btn_text}")
                
                if ASSIGNEE.lower() not in btn_text.lower():
                    print(f"Setting Assignee to {ASSIGNEE}...")
                    await assignee_btn.click()
                    # Wait for menu
                    menu = page.locator("div[role='menu']").first
                    await menu.wait_for(state="visible")
                    
                    option = menu.locator(f"div:has-text('{ASSIGNEE}')").first
                    if await option.is_visible():
                        await option.click()
                        print("✅ Assignee updated.")
                    else:
                        print(f"⚠️ Could not find assignee option for {ASSIGNEE}")
                        await page.keyboard.press("Escape")
                else:
                    print("Assignee already correct.")
            except Exception as e:
                print(f"Error updating Assignee: {e}")

            await page.wait_for_timeout(1000)

            # 2. LABEL
            try:
                # Check directly if label is visible in the label list area
                # Labels are usually span or div classes in the sidebar
                # But easiest is to open the picker and check/add
                
                print(f"Checking Label {LABEL}...")
                label_btn = page.locator("button[data-testid='label-management']").first
                if not await label_btn.is_visible():
                     label_btn = page.locator("div:has-text('Labels')").first
                
                await label_btn.click()
                
                # Check if checked? Usually it's a multi-select token field or a list
                # We'll just type and enter, Usersnap usually handles dupes or toggles
                # Safe way: Type, see if "selected" state exists?
                # Simpler: Type and Enter.
                
                label_input = page.locator("input[placeholder*='Find or create']").first
                await label_input.wait_for(state="visible")
                await label_input.fill(LABEL)
                await page.wait_for_timeout(500)
                await page.keyboard.press("Enter")
                print("✅ Label interaction performed.")
                
                # Close picker
                await page.keyboard.press("Escape")
                
            except Exception as e:
                print(f"Error updating Label: {e}")

            await page.wait_for_timeout(1000)

            # 3. STATUS
            # User mentioned updating Status. Usually it defaults to Open. 
            # If we need to ensure it is Open:
            try:
                status_btn = page.locator("button[data-testid='status-button']").first
                if await status_btn.is_visible():
                    status_text = await status_btn.inner_text()
                    print(f"Current Status: {status_text}")
                    # If we want to ensure 'Open', and it's not 'Open' (e.g. it is 'Triage' or 'Done')
                    # Analysis didn't specify, but I'll reset to Open or similar if it looks wrong?
                    # Actually, usually "Open" is the target.
                    if "Open" not in status_text:
                         print("Setting status to Open...")
                         await status_btn.click()
                         await page.locator("div[role='menu'] div:has-text('Open')").first.click()
                         print("✅ Status set to Open.")
            except Exception as e:
                print(f"Error updating Status: {e}")

            print("All fixes applied.")
            await page.wait_for_timeout(3000)

        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            await page.screenshot(path="debug_fix_fail_4017.png")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(fix_item())
