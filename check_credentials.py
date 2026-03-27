import os
import sys
from dotenv import load_dotenv

def check_credentials():
    print("🔍 Checking Environment Credentials...\n")
    
    # Load .env explicitly if needed, or rely on auto-load
    load_dotenv()
    
    required_keys = {
        "INTERCOM_API_TOKEN": "Required for checking context/conversations",
        "CLICKUP_API_TOKEN": "Required for WBR Reporting & Slack Alerts",
        "CHARGEBEE_SITE": "Required for Invoice Automation",
        "CHARGEBEE_API_KEY": "Required for Invoice Automation",
        "FULLSTORY_API_KEY": "Required for User Session Summaries",
        "SLACK_BOT_TOKEN": "Required for sending Alerts (optional if using Webhook)",
        # "GOOGLE_SHEETS_JSON": "Required for WBR Sheets update" # Often a file path, check separately
    }
    
    missing = []
    present = []
    
    for key, desc in required_keys.items():
        val = os.getenv(key)
        if val and val.strip():
            present.append(key)
            print(f"✅ {key}: Found")
        else:
            missing.append((key, desc))
            print(f"❌ {key}: MISSING ({desc})")
            
    print("\n" + "="*40)
    if missing:
        print(f"⚠️  {len(missing)} Required Credentials Missing.")
        print("Please add them to your .env file:")
        print(f"File: {os.path.abspath('.env')}\n")
        print("Example format:")
        for key, _ in missing:
            print(f"{key}=your_value_here")
        sys.exit(1)
    else:
        print("🎉 All systems go! You are ready to run the automations.")
        sys.exit(0)

if __name__ == "__main__":
    check_credentials()
