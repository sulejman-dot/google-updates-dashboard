import asyncio
import os
from playwright.async_api import async_playwright

USERSNAP_DIRECT_URL = "https://app.usersnap.com/#/projects/31a2ba9a-4a79-42c7-9218-c8782d4a1435/list?number=4017"

async def dump_html():
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
            
            # Dismiss popups
            await page.mouse.click(10, 100)
            
            content = await page.content()
            with open("debug_4017.html", "w") as f:
                f.write(content)
            print("Dumped HTML to debug_4017.html")
            
            # Also text content for quick check
            text = await page.inner_text("body")
            print("--- Page Text Sample ---")
            print(text[:1000])

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(dump_html())
