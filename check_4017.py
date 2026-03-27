import asyncio
import os
from playwright.async_api import async_playwright

# Usersnap #4017
USERSNAP_ITEM_ID = "#4017"
USERSNAP_LIST_URL = "https://app.usersnap.com/#/projects/31a2ba9a-4a79-42c7-9218-c8782d4a1435/list"

async def check_item():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        # Increase timeout for slow loading
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=['--start-maximized']
        )
        
        page = await context.new_page()
        try:
            print(f"Navigating to {USERSNAP_LIST_URL}")
            await page.goto(USERSNAP_LIST_URL)
            await page.wait_for_timeout(5000)
            
            # Login check
            if "login" in page.url:
                print("⚠️ Please log in manually.")
                await page.wait_for_timeout(60000)
                
            # Search for Item
            print(f"Searching for {USERSNAP_ITEM_ID}...")
            # Use the robust selector from update script
            search_input = page.locator('input[placeholder="Search & Filter"], input[placeholder*="Search"], input[class*="searchInput"]').first
            
            try:
                await search_input.wait_for(state="visible", timeout=10000)
                await search_input.click()
                await search_input.fill("")
                for _ in range(5): await page.keyboard.press("Backspace")
                await search_input.fill(USERSNAP_ITEM_ID)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"Search failed: {e}")
                # Fallback click
                await page.locator("div[class*='searchContainer']").first.click(force=True)
                await page.keyboard.type(USERSNAP_ITEM_ID)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(3000)
            
            # Open item
            # Look for exact text in list
            item = page.locator(f"div[class*='list-item'] >> text={USERSNAP_ITEM_ID}").first
            if await item.count() == 0:
                 # Fallback generic text
                 item = page.locator(f"text={USERSNAP_ITEM_ID}").first
            
            if await item.count() > 0:
                print("Found item. Opening...")
                await item.click()
                await page.wait_for_timeout(5000)
                
                # Scrape Content
                content = await page.content()
                
                print("--- Item Content Analysis ---")
                
                import re
                # Find Links
                urls = re.findall(r'https?://[^\s<"]+', content)
                intercom_links = [u for u in urls if "intercom.com" in u]
                clickup_links = [u for u in urls if "clickup.com" in u]
                
                print(f"Intercom Links: {intercom_links}")
                print(f"ClickUp Links: {clickup_links}")
                
            else:
                print("❌ Item not found.")
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(check_item())
