import asyncio
from playwright.async_api import async_playwright
import os

async def debug_label_ui():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            slow_mo=500,
            args=['--start-maximized']
        )
        page = await context.new_page()
        
        try:
            print("Navigating to item #3964...")
            await page.goto("https://app.usersnap.com/l/feedback/98467de3-2cad-43a7-943d-6abc095ab406")
            await page.wait_for_timeout(5000)
            
            print("Attempting to click 'Add label'...")
            # Try specific button first
            add_label_btn = page.locator("button:has-text('Add label'), button[aria-label='Add label']").first
            if await add_label_btn.is_visible():
                print("Clicked specific Add Label button")
                await add_label_btn.click()
            else:
                print("Clicked Labels section header fallback")
                labels_header = page.locator("div:has-text('Labels')").first
                await labels_header.click()
            
            await page.wait_for_timeout(2000)
            
            # Take screenshot of open picker
            screenshot_path = os.path.join(os.getcwd(), "debug_label_picker.png")
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            
            # Dump HTML of potentially relevant inputs
            inputs = page.locator("input, [contenteditable]")
            count = await inputs.count()
            print(f"Found {count} inputs/editables:")
            for i in range(count):
                el = inputs.nth(i)
                if await el.is_visible():
                    placeholder = await el.get_attribute("placeholder") or "No placeholder"
                    outer_html = await el.evaluate("el => el.outerHTML")
                    print(f"Input {i}: Placeholder='{placeholder}' | HTML: {outer_html[:100]}...")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(debug_label_ui())
