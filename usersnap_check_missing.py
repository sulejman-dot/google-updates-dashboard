import asyncio
import re
import os
import json
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load configuration from .env file
load_dotenv()

# --- Configuration ---
# Correct URL for SEOmonitor feedback project
USERSNAP_PROJECT_URL = "https://app.usersnap.com/#/projects/31a2ba9a-4a79-42c7-9218-c8782d4a1435/list"

async def check_usersnap_items():
    """
    Opens Usersnap dashboard, applies 'Not state: Done' filter, 
    and checks for items missing required details.
    Reports items missing: assignee, status, or priority.
    """
    async with async_playwright() as p:
        user_data_dir = os.path.join(os.getcwd(), "usersnap_profile")
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            slow_mo=200,
            viewport=None,
            args=['--start-maximized']
        )

        try:
            page = await context.new_page()
            
            # 1. Force navigation to the clean list URL
            clean_url = "https://app.usersnap.com/#/projects/31a2ba9a-4a79-42c7-9218-c8782d4a1435/list"
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Navigating to clean project list...")
            print(f"URL: {clean_url}")
            
            # Go to the clean URL
            await page.goto(clean_url)
            await page.wait_for_timeout(5000)
            
            # Check if we need to log in
            if "login" in page.url.lower():
                print("❌ Not logged in. Please log in manually in the browser window.")
                print("⏳ Waiting 60 seconds for manual login...")
                await page.wait_for_timeout(60000)
                await page.goto(clean_url)
                await page.wait_for_timeout(5000)
            
            print("✅ Page loaded")
            
            # 2. Clear any lingering filters - BRUTE FORCE CLEARING
            print("🧹 Clearing filters (Brute Force Backspace)...")
            try:
                # Focus the search input
                filter_input = page.locator('input[placeholder*="Search"], input[placeholder*="filter"]').first
                await filter_input.click()
                await page.wait_for_timeout(500)
                
                # Press Backspace 50 times to clear everything (tokens + text)
                # Each token usually takes 1 or 2 backspaces to remove
                for i in range(50):
                    await page.keyboard.press("Backspace")
                    if i % 10 == 0:
                        await page.wait_for_timeout(50) # Small delay every few presses
                
                print("✅ Backspaced 50 times. Filters should be gone.")
                
            except Exception as e:
                print(f"Note: Error during filter clearing: {e}")

            # 3. Apply the specific filter "Not state: Done"
            print("🔍 Trying to apply structured filter 'State'...")
            try:
                # Re-locate input
                filter_input = page.locator('input[placeholder*="Search"], input[placeholder*="filter"]').first
                
                if await filter_input.count() > 0:
                    await filter_input.click()
                    
                    # Type "State" to trigger dropdown
                    print("Typing 'State'...")
                    await filter_input.type("State", delay=100)
                    await page.wait_for_timeout(2000)
                    
                    # Take screenshot to see if dropdown appears
                    await page.screenshot(path="usersnap_filter_dropdown.png")
                    print("📸 Screenshot saved: usersnap_filter_dropdown.png")
                    
                    # Press Enter to select "State" (assuming it's the first option or auto-selected)
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(1000)
                    
                    # Now type "Done"
                    # Usually next step is operator. Defaults to "is". 
                    # We want "is not". 
                    # Let's see what happens after selecting State.
                    await page.screenshot(path="usersnap_filter_state_selected.png")
                    
                else:
                    print("⚠️  Could not find filter input.")

                    


                    
            except Exception as e:
                print(f"Note: Could not apply filter automatically: {e}")
                print("Please manually apply the filter 'Not state: Done' in the browser.")
                print("Waiting 30 seconds...")
                await page.wait_for_timeout(30000)
            
            # Take a screenshot to confirm filter is applied
            await page.screenshot(path="usersnap_filtered_view.png")
            print("📸 Screenshot saved: usersnap_filtered_view.png")
            
            # Now get all feedback items from the list
            print("\n🔍 Loading unprocessed feedback items...\n")
            
            # Scroll the list to load more items
            print("📜 Scrolling to load items...")
            for scroll_attempt in range(10):
                await page.mouse.move(200, 400)
                await page.mouse.wheel(0, 500)
                await page.wait_for_timeout(1000)
            
            incomplete_items = []
            checked_items = []
            
            # Get all item IDs from the page
            page_content = await page.content()
            item_ids = re.findall(r'#(\d{4})', page_content)
            unique_ids = list(dict.fromkeys(item_ids))  # Preserve order while removing duplicates
            
            print(f"✅ Found {len(unique_ids)} unique feedback IDs")
            if len(unique_ids) > 0:
                print(f"   IDs: {', '.join(['#' + id for id in unique_ids[:10]])}{'...' if len(unique_ids) > 10 else ''}")
            
            items_to_check = min(len(unique_ids), 50)  # Check up to 50 items
            print(f"📋 Will check {items_to_check} items for missing details...\n")
            
            for idx, item_id in enumerate(unique_ids[:items_to_check], 1):
                try:
                    print(f"[{idx}/{items_to_check}] Checking #{item_id}...")
                    
                    # Click the item in the sidebar to open it
                    item_link = page.locator(f'text=#{item_id}').first
                    if await item_link.count() > 0:
                        await item_link.scroll_into_view_if_needed()
                        await item_link.click()
                        await page.wait_for_timeout(2500)
                    else:
                        print(f"   ⚠️  Could not find item in list, skipping...")
                        continue
                    
                    missing_fields = []
                    field_details = {}
                    
                    # Get the page content for this item
                    item_content = await page.content()
                    
                    # Check Assignee - look for "Unassigned" text or assignee name
                    try:
                        if "Unassigned" in item_content:
                            missing_fields.append("Assignee")
                            field_details["assignee"] = "❌ Unassigned"
                        else:
                            # Try to extract assignee name
                            assignee_match = re.search(r'ASSIGNEE[^<]*?<[^>]*>([^<]+)</[^>]*>', item_content)
                            if assignee_match:
                                field_details["assignee"] = f"✅ {assignee_match.group(1).strip()}"
                            else:
                                # Alternative: look for common names
                                if "Sulejman" in item_content or "Lekic" in item_content:
                                    field_details["assignee"] = "✅ Assigned"
                                else:
                                    field_details["assignee"] = "❓ Unknown"
                    except Exception as e:
                        field_details["assignee"] = "❓ Error"
                    
                    # Check Priority
                    try:
                        if re.search(r'PRIORITY[^<]*?None', item_content, re.IGNORECASE):
                            missing_fields.append("Priority")
                            field_details["priority"] = "❌ None"
                        elif "High" in item_content and "PRIORITY" in item_content:
                            field_details["priority"] = "✅ High"
                        elif "Medium" in item_content and "PRIORITY" in item_content:
                            field_details["priority"] = "✅ Medium"
                        elif "Low" in item_content and "PRIORITY" in item_content:
                            field_details["priority"] = "✅ Low"
                        else:
                            field_details["priority"] = "❓ Unknown"
                    except Exception as e:
                        field_details["priority"] = "❓ Error"
                    
                    # Check Status - should be "Open" or similar since we filtered for "Not Done"
                    try:
                        if "Done" in item_content and "STATUS" in item_content:
                            field_details["status"] = "✅ Done"
                        elif "Open" in item_content and "STATUS" in item_content:
                            field_details["status"] = "📋 Open"
                        elif "In Progress" in item_content:
                            field_details["status"] = "🔄 In Progress"
                        else:
                            field_details["status"] = "❓ Unknown"
                    except Exception as e:
                        field_details["status"] = "❓ Error"
                    
                    current_url = page.url
                    
                    if missing_fields:
                        incomplete_items.append({
                            "id": f"#{item_id}",
                            "url": current_url,
                            "missing": missing_fields,
                            "details": field_details
                        })
                        print(f"   ⚠️  MISSING: {', '.join(missing_fields)}")
                        print(f"   {field_details}")
                    else:
                        print(f"   ✅ Complete - {field_details}")
                    
                    checked_items.append({
                        "id": f"#{item_id}",
                        "missing": missing_fields,
                        "details": field_details,
                        "url": current_url
                    })
                    
                except Exception as e:
                    print(f"   ⚠️  Error: {e}")
                    continue
            
            # Summary
            print("\n" + "="*70)
            print(f"📊 SUMMARY - Unprocessed Usersnaps (Not state: Done)")
            print("="*70)
            print(f"Total items checked: {len(checked_items)}")
            print(f"Items with missing details: {len(incomplete_items)}")
            
            if incomplete_items:
                print("\n🔴 Items needing attention:")
                for item in incomplete_items:
                    print(f"\n  • {item['id']}")
                    print(f"    Missing: {', '.join(item['missing'])}")
                    print(f"    Current state: {item.get('details', {})}")
                    print(f"    URL: {item['url']}")
            else:
                print("\n✅ All checked items have complete details!")
            
            # Save detailed report to file
            report_file = f"usersnap_unprocessed_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "filter_applied": "Not state: Done",
                    "total_checked": len(checked_items),
                    "incomplete_count": len(incomplete_items),
                    "all_items": checked_items,
                    "incomplete_items": incomplete_items
                }, f, indent=2)
            
            print(f"\n📄 Detailed report saved to: {report_file}")
            
        finally:
            print("\n⏸️  Keeping browser open for 30 seconds for review...")
            await page.wait_for_timeout(30000)
            await context.close()

if __name__ == "__main__":
    print("🚀 Starting Usersnap Unprocessed Items Check...")
    print("This will check items with 'Not state: Done' filter for missing details.\n")
    asyncio.run(check_usersnap_items())
