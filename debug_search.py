import asyncio
import os
from playwright.async_api import async_playwright

USERSNAP_PROJECT_URL = "https://app.usersnap.com/#/projects/31a2ba9a-4a79-42c7-9218-c8782d4a1435/list"

async def debug_search():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=['--start-maximized']
        )
        
        page = await context.new_page()
        try:
            print(f"Navigating to {USERSNAP_PROJECT_URL}")
            await page.goto(USERSNAP_PROJECT_URL)
            await page.wait_for_timeout(8000)
            
            # Dump content
            content = await page.content()
            with open("debug_list.html", "w") as f:
                f.write(content)
            print("Dumped list HTML to debug_list.html")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(debug_search())
