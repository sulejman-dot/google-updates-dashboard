# Usersnap-Intercom Browser Synchronization Guide

Since Usersnap API access is unavailable on the free plan, this script automates the synchronization by driving a browser (using Playwright).

## 🚀 Setup Instructions

1. **Install Python**: Ensure you have Python 3.8+ installed.
2. **Install Dependencies**:
   Open your terminal and run:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Configure the Script**:
   Open `usersnap_browser_sync.py` and personalize the `items_to_sync` list at the bottom of the file with the actual IDs and data you want to process.

## 🛠️ How to Run

Run the script from your terminal:
```bash
python usersnap_browser_sync.py
```

### What to Expect:
- A browser window will open.
- **Login**: If prompted, manually log in to Usersnap. The script will wait for you to reach the dashboard.
- **Automation**: Once logged in, the script will automatically search for each ID (#XXXX), open it, update the assignee, priority, add the ClickUp URL as a note, and set the status to "Done".

## ⚠️ Notes
- **Selectors**: If Usersnap updates their website layout, the selectors in the script (e.g., `text="Unassigned"`) might need updating.
- **Headless Mode**: The script currently runs with `headless=False` so you can monitor the progress and handle logins.
