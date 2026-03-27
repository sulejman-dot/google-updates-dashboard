import asyncio
import os
from playwright.async_api import async_playwright

# Update Targets
ITEM_ID = "#4018"
ASSIGNEE = "Ioana"
LABELS = ["Bug"]
PRIORITY = "Low" # Default/None from analysis, but UI needs something? "None" is valid.
# Status? Let's leave status alone unless requested.

USERSNAP_LIST_URL = "https://app.usersnap.com/#/projects/31a2ba9a-4a79-42c7-9218-c8782d4a1435/list"

async def update_item():
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
            print(f"Navigating to {USERSNAP_LIST_URL}")
            await page.goto(USERSNAP_LIST_URL)
            await page.wait_for_timeout(5000)
            
            # Login check
            if "login" in page.url:
                print("⚠️ Please log in manually.")
                await page.wait_for_timeout(60000)
            
            # Search for ITEM_ID
            print(f"Searching for {ITEM_ID}...")
            
            # Try multiple selectors for the search input
            search_input = page.locator('input[placeholder="Search & Filter"], input[placeholder*="Search"], input[class*="searchInput"]').first
            
            try:
                await search_input.wait_for(state="visible", timeout=10000)
                await search_input.click()
                # Clear existing text
                await search_input.fill("")
                for _ in range(5): await page.keyboard.press("Backspace")
                
                await search_input.fill(ITEM_ID)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"Search input interaction failed: {e}")
                print("Trying to click search icon/container...")
                # Fallback: click identifying parent container
                await page.locator("div[class*='searchContainer'], div[class*='filterBar']").first.click(force=True)
                await page.keyboard.type(ITEM_ID)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(3000)
            
            # Open item - wait for result
            # We look for the text in the list
            item_selector = f"div[class*='list-item'] >> text={ITEM_ID}"
            # Or just text
            item = page.locator(f"div:has-text('{ITEM_ID}')").last # last might be safer if there are duplicates in DOM, but first is usually list
            # Actually, let's use the one that looks like a list item or title
            
            # Specific check for No Results
            if await page.locator("text=No feedback found").is_visible():
                print("❌ Search returned no results.")
                return

            # Click the item
            print(f"Clicking item #{ITEM_ID}...")
            # Use a broad text match that is clickable
            await page.locator(f"text={ITEM_ID}").first.click()
            await page.wait_for_timeout(3000)

            
            print(f"Updating #4018...")
            
            # 1. Update Assignee
            # Note: "Ioana" might match "Ioana X"
            try:
                assignee_btn = page.locator("button[data-testid='assignee-button']").first
                if await assignee_btn.is_visible():
                    current = await assignee_btn.get_attribute("aria-label") or ""
                    if ASSIGNEE not in current:
                        await assignee_btn.click()
                        await page.locator(f"div[role='menu'] div:has-text('{ASSIGNEE}')").first.click()
                        print(f"✅ Assignee set to {ASSIGNEE}")
                    else:
                        print(f"Assignee already {ASSIGNEE}")
            except Exception as e:
                print(f"Error setting assignee: {e}")

            # 2. Add Label
            try:
                # Add label logic
                add_label_btn = page.locator("button[data-testid='label-management']").first
                if await add_label_btn.is_visible():
                    await add_label_btn.click()
                else:
                    await page.locator("div:has-text('Labels')").first.click()
                
                label_input = page.locator("input[placeholder*='Find or create label']").first
                await label_input.wait_for(state="visible")
                
                for label in LABELS:
                    await label_input.fill(label)
                    await page.wait_for_timeout(500)
                    await page.keyboard.press("Enter")
                    print(f"✅ Added label: {label}")
                
                await page.keyboard.press("Escape")
            except Exception as e:
                print(f"Error adding labels: {e}")
                
            print("Update Complete!")
            await page.wait_for_timeout(2000)

        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            await page.screenshot(path="debug_update_fail.png")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(update_item())
