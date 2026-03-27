import asyncio
from playwright.async_api import async_playwright
import os
import sys

# Import the sync logic from the main script
# We'll just copy the sync_to_usersnap function or import it if possible
# To avoid import issues with global vars, I'll redefine a minimal version or import
# Let's try importing, but we need to mock constants if they are used.
# Actually, let's just copy the relevant sync logic to verify IT specifically without side effects.

USERSNAP_BASE_URL = "https://app.usersnap.com/l/feedback/54180ff6-8739-44d3-a743-e0e89b792fb4"

async def sync_to_usersnap_test(data, context):
    page = await context.new_page()
    try:
        print(f"--- Processing Test Item {data['usersnap_id']} ---")
        
        # Navigate
        await page.goto(data['direct_url'])
        await page.wait_for_timeout(5000)

        # Check login
        if "login" in page.url:
            print("⚠️ Login required. PLEASE LOG IN manually in the browser.")
            await page.wait_for_timeout(30000)
        
        # 1. Labels
        if data['labels']:
            print(f"Attempting to add labels: {data['labels']}")
            try:
                # Find "Add label" button
                add_label_btn = page.locator("button:has-text('Add label'), button[aria-label='Add label']").first
                if await add_label_btn.is_visible():
                     await add_label_btn.click()
                else:
                     # fallback
                     labels_header = page.locator("div:has-text('Labels')").first
                     await labels_header.click()
                
                await page.wait_for_timeout(1000)
                
                # Input for labels
                label_input = page.locator("input[placeholder*='Find or create label']").first
                await label_input.wait_for(state="visible", timeout=3000)
                
                for label in data['labels']:
                    await label_input.fill(label)
                    await page.wait_for_timeout(1000) # Wait for suggest
                    await page.keyboard.press("Enter")
                    print(f"Added label: {label}")
                    
                await page.keyboard.press("Escape")
                
            except Exception as e:
                print(f"❌ Label sync failed: {e}")

        # 2. Priority
        if data['priority'] == "High":
             print("Attempting to set High Priority")
             # Add priority logic here if needed for test
             pass

        print("✅ Test Sync Complete")
        # Keep open briefly to verify
        await page.wait_for_timeout(5000)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await page.close()

async def main():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            slow_mo=500,
            args=['--start-maximized']
        )
        
        # Mock Data for #3964 but WITH LABELS
        mock_item = {
            "usersnap_id": "#3964",
            "direct_url": "https://app.usersnap.com/l/feedback/98467de3-2cad-43a7-943d-6abc095ab406",
            "assignee": "Sulejman",
            "priority": "High", # Force high to test
            "labels": ["Test-Automation-Label"], # Mock label
            "clickup_url": "https://app.clickup.com/t/test"
        }
        
        await sync_to_usersnap_test(mock_item, context)
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
