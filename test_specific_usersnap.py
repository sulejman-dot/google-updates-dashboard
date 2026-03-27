import asyncio
import os
from playwright.async_api import async_playwright
# Import the actual sync function to test IT, not a copy
from usersnap_browser_sync import sync_to_usersnap, USERSNAP_BASE_URL

# Test Configuration for #4026
TEST_DATA = {
    "usersnap_id": "#4026",
    "direct_url": "", # Force search to test new filter clearing logic
    "assignee": "Sulejman",
    "priority": "High", # Assuming we want to test High priority
    "labels": ["Bug"], # Testing "Bug" label scenario (ClickUp URL present, no 'product')
    "clickup_url": "https://app.clickup.com/t/123456" # Mock URL to trigger Note logic
}

async def test_update_usersnap_live():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            slow_mo=1000, # Slower for observation
            viewport=None,
            args=['--start-maximized']
        )
        
        print(f"🚀 Starting Test for {TEST_DATA['usersnap_id']}...")
        print(f"📝 Test Data: {TEST_DATA}")
        print(f"🌍 Navigating to Base URL: {USERSNAP_BASE_URL}")

        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(USERSNAP_BASE_URL)
        await page.wait_for_timeout(5000) # Wait for load

        success = await sync_to_usersnap(TEST_DATA, context, dry_run=False)
        
        if success:
            print("✅ Test execution reported success.")
        else:
            print("❌ Test execution reported failure.")
            
        # Keep open briefly for manual check
        print("Waiting 10s for manual inspection...")
        await asyncio.sleep(10)
        await context.close()

if __name__ == "__main__":
    asyncio.run(test_update_usersnap_live())
