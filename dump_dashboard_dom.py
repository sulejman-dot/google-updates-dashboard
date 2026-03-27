import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

USERSNAP_BASE_URL = "https://app.usersnap.com/#/projects/31a2ba9a-4a79-42c7-9218-c8782d4a1435/list"

async def main():
    print("🚀 Starting Dashboard DOM Dump...")
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True, # Headless is fine for dumping
            args=['--start-maximized']
        )
        
        page = await context.new_page() if not context.pages else context.pages[0]
        
        print(f"Navigating to {USERSNAP_BASE_URL}...")
        await page.goto(USERSNAP_BASE_URL)
        await page.wait_for_timeout(10000) # Wait for full load

        print("Dumping DOM...")
        content = await page.content()
        with open("dashboard_dom.html", "w") as f:
            f.write(content)
        print("✅ DOM dumped to dashboard_dom.html")
        
        # Take a screenshot too for context
        await page.screenshot(path="dashboard_view.png")
        print("Screenshot saved to dashboard_view.png")

        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
