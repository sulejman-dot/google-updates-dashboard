import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

USERSNAP_BASE_URL = "https://app.usersnap.com/#/projects/31a2ba9a-4a79-42c7-9218-c8782d4a1435/list"

async def main():
    print("🚀 Starting Filter Logic Test...")
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            slow_mo=1000, # Go slower to see interactions
            args=['--start-maximized']
        )
        
        page = await context.new_page() if not context.pages else context.pages[0]
        
        print(f"Navigating to {USERSNAP_BASE_URL}...")
        await page.goto(USERSNAP_BASE_URL)
        await page.wait_for_timeout(5000)

        # 1. Locate Filter Input
        print("Looking for 'Search & Filter' input...")
        try:
            # Fallback selector strategy
            filter_input = page.locator('div[class*="filterContainer"] input, input[placeholder*="Search"], input[placeholder*="Filter"]').first
            await filter_input.wait_for(state="visible", timeout=10000)
            print("✅ Filter input found.")
            
            # 2. Apply "Status is not Done"
            # Strategy: Click -> Type 'Status' -> Select 'Status' -> Type 'is not' (or select) -> Type 'Done'
            # Note: The UI might be "Status" -> "is not" -> "Done" as pills. 
            # We will try to interact step-by-step.
            
            await filter_input.click()
            await page.wait_for_timeout(1000)

            # 3. Click "Open" from the dropdown
            print("Looking for 'Open' option in dropdown...")
            # Based on the screenshot, "Open" is a list item. 
            # We'll look for it by text. 
            # Note: Trying exact match or distinct selector to avoid false positives.
            # The screenshot shows "Open" under "STATE".
            
            try:
                # Try to find the exact text "Open" that is visible
                open_option = page.locator("div[role='option'], li, div").filter(has_text="Open").first
                # Or more generically just text if role is not clear from DOM dump earlier (DOM dump didn't show dropdown)
                # Let's try a robust text locator.
                open_option = page.locator("text=Open").first
                
                await open_option.wait_for(state="visible", timeout=5000)
                await open_option.click()
                print("✅ Clicked 'Open'.")
                
            except Exception as e:
                print(f"⚠️ Could not click 'Open' easily: {e}")
                # Fallback: Type "Open" and press Enter if clicking fails
                print("Fallback: Typing 'Open'...")
                await filter_input.type("Open")
                await page.keyboard.press("Enter")
            
            print("✅ Filter sequence finished. Pausing for verification...")
            
        except Exception as e:
            print(f"❌ Error interacting with filter: {e}")
            await page.screenshot(path="debug_filter_fail.png")

        # Keep open for user to see
        await page.wait_for_timeout(60000)
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
