import asyncio
from playwright.async_api import async_playwright
import os

async def take_screenshot():
    async with async_playwright() as p:
        # Use the same profile as the automation script to reuse login session
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False, # Headless=False to see what's happening if needed
            slow_mo=500
        )
        page = await context.new_page()
        
        try:
            print("Navigating to item #3964...")
            await page.goto("https://app.usersnap.com/l/feedback/98467de3-2cad-43a7-943d-6abc095ab406")
            
            # Wait for key elements to load
            try:
                await page.wait_for_selector('div[class*="Details"]', timeout=15000)
            except:
                print("Could not find Details element, possibly login required or slow load.")
            
            # Take screenshot
            screenshot_path = os.path.join(os.getcwd(), "verification_3964.png")
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            
            # Also extract text details for programmatic verification
            content = await page.content()
            print("Assignee: 'Sulejman' in content?", "Sulejman" in content)
            print("Status: 'Done' in content?", "Done" in content)
            print("Note: 'app.clickup.com' in content?", "app.clickup.com" in content)
            
            # Check for Priority
            # Usersnap usually displays priority as text "High", "Medium", "Low", or "None"
            # It might be in a button or span.
            print("Priority 'High' visible?", "High" in content)
            
            # Check for Labels
            # Labels often appear as colored badges. We might just look for common label names or the container.
            # Let's print the text of elements that look like labels if possible, or just dump text around "Labels"
            try:
                # Naive check for now
                labels_section = page.locator("div:has-text('Labels')").first
                if await labels_section.count() > 0:
                     print("Labels section found.")
                     # Try to get text of actual labels
                     # This depends on DOM structure, but let's try to grab the whole content text to manually inspect output
                     pass
            except:
                pass
                
            print(f"Content length: {len(content)}")


        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(take_screenshot())
