import asyncio
import os
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            viewport={'width': 1280, 'height': 800}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        url = "https://app.usersnap.com/l/feedback/54180ff6-8739-44d3-a743-e0e89b792fb4?item=#3983"
        print(f"Navigating to {url}...")
        await page.goto(url)
        await page.wait_for_timeout(10000) # Wait for load
        
        # Take initial screenshot
        await page.screenshot(path="debug_init.png")
        
        # Look for "Add note" and click it
        try:
            add_note = page.locator("text='Add note'").first
            await add_note.click()
            print("Clicked 'Add note'")
            await page.wait_for_timeout(2000)
            await page.screenshot(path="debug_after_click.png")
        except Exception as e:
            print(f"Failed to click 'Add note': {e}")
            
        # Dump DOM
        content = await page.content()
        with open("usersnap_dom.html", "w") as f:
            f.write(content)
        print("DOM dumped to usersnap_dom.html")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(debug())
