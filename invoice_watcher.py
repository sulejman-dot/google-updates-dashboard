import os
import time
import zipfile
import shutil
import tempfile
import urllib.request
import urllib.parse
import json
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import your existing processing script
from invoice_automation_csv import main as process_invoices

# Get environment variables (or rely on them being in the actual .env and loaded by bash if preferred,
# but we'll parse the .env directly just to be 100% safe)
def get_slack_webhook():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('SLACK_WEBHOOK_URL='):
                    return line.strip().split('=', 1)[1].strip()
    return None

FOLDER_TO_WATCH = os.path.expanduser("~/Desktop/Chargebee_Invoices")
PROCESSED_FOLDER = os.path.join(FOLDER_TO_WATCH, "Processed")
TEST_SHEET_URL = "https://docs.google.com/spreadsheets/d/191g9fIbjKi-r2hA_5PxbyVfVN3rx7e5rFlfEGH5NfDM/edit"
SLACK_WEBHOOK = get_slack_webhook()

# Setup logging
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'magic_folder.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler() # Also print to console
    ]
)

def send_slack_notification(message):
    if not SLACK_WEBHOOK:
        logging.warning("No Slack Webhook URL found. Cannot send notification.")
        return
        
    try:
        data = json.dumps({'text': message}).encode('utf-8')
        req = urllib.request.Request(SLACK_WEBHOOK, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            if response.getcode() != 200:
                logging.error(f"Failed to post to Slack: {response.getcode()}")
    except Exception as e:
        logging.error(f"Error sending Slack notification: {e}")

class InvoiceZipHandler(FileSystemEventHandler):
    def on_created(self, event):
        # We only care about .zip files being created
        if not event.is_directory and event.src_path.lower().endswith('.zip'):
            logging.info(f"✨ Magic Folder detected new file: {os.path.basename(event.src_path)}")
            # Add a small delay to ensure the browser has completely finished writing the file
            time.sleep(3)
            self.process_zip(event.src_path)

    def process_zip(self, zip_path):
        filename = os.path.basename(zip_path)
        logging.info(f"📦 Extracting {filename}...")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                csv_path = os.path.join(temp_dir, "Invoices.csv")
                
                if os.path.exists(csv_path):
                    logging.info("📄 Found Invoices.csv! Starting Google Sheets processing...")
                    
                    # Run the updater and get the counts
                    results = process_invoices(TEST_SHEET_URL, temp_dir)
                    
                    if results:
                        s_count = results.get('Sulejman', 0)
                        k_count = results.get('Katty', 0)
                        total = s_count + k_count
                        
                        logging.info(f"✅ Processing complete! Added {total} new clients.")
                        
                        slack_msg = (
                            f"✨ *Magic Folder Processed New Chargebee Export* ✨\n"
                            f"File: `{filename}`\n"
                            f"Added *{total}* new unpaid invoices to the Tracker.\n"
                            f"• Sulejman: {s_count}\n"
                            f"• Katty: {k_count}"
                        )
                        send_slack_notification(slack_msg)
                    else:
                        logging.warning("⚠️ Script completed but returned None. Perhaps an error occurred.")
                        send_slack_notification(f"⚠️ Magic Folder ran on `{filename}` but encountered an issue or nothing was processed.")
                        
                else:
                    logging.error(f"❌ Could not find Invoices.csv inside the ZIP file.")
                    send_slack_notification(f"❌ Magic Folder failed on `{filename}`: missing `Invoices.csv` inside the zip.")
            
            # Clean up: Move the processed ZIP to the "Processed" folder
            dest_path = os.path.join(PROCESSED_FOLDER, filename)
            if os.path.exists(dest_path):
                name, ext = os.path.splitext(filename)
                dest_path = os.path.join(PROCESSED_FOLDER, f"{name}_{int(time.time())}{ext}")
                
            shutil.move(zip_path, dest_path)
            logging.info(f"📁 Moved ZIP to Processed folder: {os.path.basename(dest_path)}")
            logging.info("⏳ Magic Folder is ready and waiting for the next file...\n")
            
        except zipfile.BadZipFile:
            logging.error("❌ Error: Invalid or corrupted ZIP file. Maybe it's still downloading?")
        except Exception as e:
            logging.error(f"❌ Unexpected error processing zip: {e}")

if __name__ == "__main__":
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)
    
    event_handler = InvoiceZipHandler()
    observer = Observer()
    observer.schedule(event_handler, FOLDER_TO_WATCH, recursive=False)
    
    logging.info(f"✨ Magic Folder Watcher is Active! ✨")
    logging.info(f"Watching: {FOLDER_TO_WATCH}")
    logging.info(f"Logging to: {log_file}")
    logging.info("Press Ctrl+C to stop.\n")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
