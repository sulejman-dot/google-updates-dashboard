import asyncio
import os
from playwright.async_api import async_playwright

ITEM_ID = "#4017"
NOTE = "https://app.clickup.com/t/869bxghjz"
USERSNAP_DIRECT_URL = "https://app.usersnap.com/#/projects/31a2ba9a-4a79-42c7-9218-c8782d4a1435/list?number=4017"

async def add_note():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=['--start-maximized']
        )
        
        page = await context.new_page()
        try:
            print(f"Navigating to {USERSNAP_DIRECT_URL}")
            await page.goto(USERSNAP_DIRECT_URL)
            await page.wait_for_timeout(8000)
            
            # Ensure stable
            await page.wait_for_load_state("networkidle")
            
            # Click title/body to dismiss any popups
            await page.mouse.click(100, 100)
            await page.wait_for_timeout(1000)

            # Check if note exists
            content_text = await page.locator("main").inner_text()
            if NOTE in content_text:
                print("✅ Note already exists.")
            else:
                print("Adding ClickUp Note...")
                # Try clicking the "Add note" tab specifically
                # The selectors might be: button containing "Add note"
                add_note_tab = page.locator("button").filter(has_text="Add note").filter(has_not=page.locator("[type='submit']")).first
                
                # Ensure it's visible
                try:
                    await add_note_tab.click(timeout=5000)
                except:
                    print("Could not click 'Add note' tab directly. Trying to find it via container...")
                    # Fallback
                    await page.click("text=Add note")
                
                await page.wait_for_timeout(1000)
                
                # Editor
                editor = page.locator(".ProseMirror").first
                await editor.click()
                await editor.type(NOTE)
                
                # Submit
                submit_btn = page.locator("button[type='submit']").filter(has_text="Add note").first
                await submit_btn.click()
                print("✅ Note added.")
                await page.wait_for_timeout(2000)

        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path="debug_note_fail.png")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(add_note())
