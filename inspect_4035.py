import asyncio
import os
from playwright.async_api import async_playwright

ITEM_ID = "#4035"
USERSNAP_PROJECT_URL = "https://app.usersnap.com/#/projects/31a2ba9a-4a79-42c7-9218-c8782d4a1435/list"

async def inspect_item():
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
            
            # Dismiss popups
            await page.mouse.click(10, 100)

            # FORCE PROJECT CONTEXT
            try:
                # Expect specific project text or tabs
                await page.wait_for_selector("text=Feedback", timeout=5000)
                print("✅ Verified inside Project.")
            except:
                print("⚠️ Could not verify Project context. We might be on Dashboard.")
                # Try clicking the project
                try:
                     await page.click("text=SEOmonitor feedback", timeout=5000)
                     await page.wait_for_timeout(5000)
                     print("Clicked project name.")
                except:
                     print("Could not recover project context.")
                     return

            # Skip Search, find in list directly
            print(f"Locating {ITEM_ID} in list directly...")
            
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
                print(f"✅ Found and clicked {ITEM_ID}.")
                await page.wait_for_timeout(3000)
                
                # Verify Sidebar opened
                await page.wait_for_selector("div[class*='detailView']", timeout=5000)
                print("Sidebar confirmed open.")
                
                # EXTRACT INFO
                print("--- Extracting Item Details ---")
                
                # Reporter
                reporter = await page.locator("button[class*='reporter']").first.inner_text()
                print(f"Reporter: {reporter}")
                
                # Title/Description
                title = await page.locator("input[name='title']").first.input_value()
                print(f"Title: {title}")
                
                # Check for links in description/comments (if accessible)
                # We might need to inspect the 'Note' or 'Comment' areas
                body_text = await page.locator("div[class*='detailView']").inner_text()
                print(f"Full Body Text Snippet: {body_text[:500]}")

            except Exception as e:
                print(f"❌ Failed to inspect item: {e}")
                await page.screenshot(path="debug_inspect_4035_fail.png")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(inspect_item())
