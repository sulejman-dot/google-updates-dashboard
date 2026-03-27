import asyncio
import os
from playwright.async_api import async_playwright

# Update Targets
ITEM_ID = "#4017"
ASSIGNEE = "Sulejman"
LABELS = ["Bug"]
NOTE = "https://app.clickup.com/t/869bxghjz"

USERSNAP_DIRECT_URL = "https://app.usersnap.com/#/projects/31a2ba9a-4a79-42c7-9218-c8782d4a1435/list?number=4017"

async def update_item():
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            # slow_mo=500,
            args=['--start-maximized']
        )
        
        page = await context.new_page()
        try:
            print(f"Navigating directly to {USERSNAP_DIRECT_URL}")
            await page.goto(USERSNAP_DIRECT_URL)
            await page.wait_for_timeout(8000) # Wait for app to load completely
            
            # Login check
            if "login" in page.url:
                print("⚠️ Please log in manually.")
                await page.wait_for_timeout(60000)
            
            # Verify item is open
            # With ?number=4017, the item should be selected and detail pane open
            print(f"Verifying {ITEM_ID} is open...")
            try:
                # Check for the item ID in the detail view or list selection
                await page.wait_for_selector(f"text={ITEM_ID}", timeout=10000)
            except:
                print("⚠️ Item ID text not immediately found, but continuing as we used direct URL...")

            print(f"Updating {ITEM_ID}...")
            
            # 1. Update Assignee
            try:
                assignee_btn = page.locator("button[data-testid='assignee-button']").first
                if await assignee_btn.is_visible():
                    current = await assignee_btn.get_attribute("aria-label") or ""
                    # "Sulejman" might be "Sulejman Lekic"
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
                
            # 3. Add Note (ClickUp Link)
            if NOTE:
                try:
                    # Check if note exists
                    content_text = await page.locator("main").inner_text()
                    if NOTE in content_text:
                        print("Note already exists.")
                    else:
                        print("Adding ClickUp Note...")
                        add_note_tab = page.locator("button:has-text('Add note')").filter(has_not=page.locator("[type='submit']")).first
                        await add_note_tab.scroll_into_view_if_needed()
                        await add_note_tab.click()
                        
                        editor = page.locator(".ProseMirror").first
                        await editor.wait_for(state="visible")
                        await editor.click()
                        await editor.type(NOTE)
                        
                        submit_btn = page.locator("button[type='submit']").filter(has_text="Add note").first
                        await submit_btn.click()
                        print("✅ Note added.")
                except Exception as e:
                    print(f"Error adding note: {e}")

            print("Update Complete!")
            await page.wait_for_timeout(2000)

        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            await page.screenshot(path="debug_update_fail_4017.png")
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(update_item())
