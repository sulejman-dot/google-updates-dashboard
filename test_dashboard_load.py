import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load env for consistency even if not strictly needed here
load_dotenv()

USERSNAP_BASE_URL = "https://app.usersnap.com/#/projects/31a2ba9a-4a79-42c7-9218-c8782d4a1435/list"

async def main():
    print("🚀 Starting Dashboard Load Test...")
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False, # Show browser
            slow_mo=500,
            args=['--start-maximized']
        )
        
        page = await context.new_page() if not context.pages else context.pages[0]
        
        print(f"Navigating to {USERSNAP_BASE_URL}...")
        await page.goto(USERSNAP_BASE_URL)
        
        # Wait for potential login
        if "login" in page.url:
             print("⚠️  Login required. Please log in manually in the browser!")
             await page.wait_for_timeout(60000)
        
        await page.wait_for_timeout(5000)

        # Confirm we are on the list
        print("Checking for filters...")
        
        # Look for the search input
        try:
            search_input = page.locator('input[placeholder*="filter"]')
            if await search_input.count() > 0:
                print("Found filter input.")
                # Attempt to clear
                await search_input.click()
                await page.keyboard.press("Meta+A")
                await page.keyboard.press("Backspace")
                print("Cleared text filters (if any).")
                
                # Try to click "X" on chips if visible
                # This is "best effort" based on previous logic
                search_container = search_input.locator("..")
                delete_btns = search_container.locator("div[class*='editorMenuItem'] svg, svg[class*='close'], svg[data-icon='times']")
                count = await delete_btns.count()
                if count > 0:
                     print(f"Found {count} filter chips/buttons. Attempting to clear...")
                     for i in range(count):
                         if await delete_btns.nth(i).is_visible():
                             await delete_btns.nth(i).click()
                             await page.wait_for_timeout(200)
            else:
                print("Filter input not found. Maybe dashboard layout changed?")
        except Exception as e:
            print(f"Error checking filters: {e}")

        print("✅ Dashboard loaded. Pausing for 30s to verify state...")
        await page.wait_for_timeout(30000)
        
        await context.close()
        print("Test complete.")

if __name__ == "__main__":
    asyncio.run(main())
