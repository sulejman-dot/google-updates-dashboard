import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from datetime import datetime

# Auth and setup
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'service_account.json'

# MOCK DATA: We will replace this with Chargebee scraping/data later
MOCK_NEW_INVOICES = [
    {
        "client": "Test Client Monthly",
        "date_issued": "10.03.2026",
        "payment_term": "NET30",
        "type": "monthly" # "prepaid" or "monthly" based on Chargebee history
    },
    {
        "client": "Test Client Prepaid",
        "date_issued": "12.03.2026",
        "payment_term": "NET30",
        "type": "prepaid"
    },
    {
        "client": "Another Monthly",
        "date_issued": "13.03.2026",
        "payment_term": "NET30",
        "type": "monthly"
    }
]

def get_sheet_client():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    client = gspread.authorize(creds)
    return client

def get_existing_clients(worksheet):
    """Returns a list of client names from the column A."""
    records = worksheet.get_all_records()
    # Assuming the column is named "Client"
    clients = [str(r.get('Client', '')).strip().lower() for r in records if r.get('Client')]
    return clients

def get_last_assigned_agent(prepaids_ws, monthly_ws):
    """
    Looks at the bottom of both sheets to see who was assigned last between Sulejman and Katty.
    This helps us continue the round-robin.
    """
    agents = []
    
    for ws in [prepaids_ws, monthly_ws]:
        records = ws.get_all_records()
        for r in records:
            agent = str(r.get('Agent', '')).strip()
            if agent in ['Sulejman', 'Katty', 'Ana & Katty', 'Ana&Katty']: 
                # We mainly track Katty and Sulejman for the new round robin
                agents.append(agent)
                
    # If we want a strict round robin, we can just default to Sulejman if we can't figure it out
    # For now, let's look at the very last valid agent in the lists
    last_agent = None
    for agent in reversed(agents):
        if agent in ['Sulejman', 'Katty']:
            last_agent = agent
            break
            
    return last_agent

def append_to_sheet(ws, invoice_data, agent):
    """Appends a new row to the worksheet matching the column structure."""
    
    # Structure: Client, Payment Term, Date issued, Agent, Convo, Status, Has extra coupon, Contact, Obs
    # We will leave Convo, Has extra coupon, Contact, Obs empty for now or put defaults
    
    row_data = [
        invoice_data['client'],
        invoice_data['payment_term'],
        invoice_data['date_issued'],
        agent,
        "", # Convo
        "Ongoing...", # Status default
        "", # Has extra coupon
        "", # Contact
        ""  # Obs
    ]
    
    ws.append_row(row_data)
    print(f"✅ Added {invoice_data['client']} to {ws.title} and assigned to {agent}")

def main(sheet_url):
    print("🔄 Connecting to Google Sheets...")
    client = get_sheet_client()
    sheet = client.open_by_url(sheet_url)
    
    try:
        prepaids_ws = sheet.worksheet("Prepaids")
        monthly_ws = sheet.worksheet("Monthly unpaid")
    except gspread.exceptions.WorksheetNotFound as e:
        print(f"❌ Could not find the required tabs: {e}")
        return

    print("📊 Fetching existing clients...")
    existing_prepaid = get_existing_clients(prepaids_ws)
    existing_monthly = get_existing_clients(monthly_ws)
    
    all_existing_clients = set(existing_prepaid + existing_monthly)
    print(f"Found {len(all_existing_clients)} total existing clients.")
    
    # Figure out whose turn it is
    last_agent = get_last_assigned_agent(prepaids_ws, monthly_ws)
    print(f"ℹ️ Last assigned agent was: {last_agent}")
    
    # Next agent to assign
    next_agent = "Katty" if last_agent == "Sulejman" else "Sulejman"

    print("\n🚀 Processing new invoices...")
    
    for inv in MOCK_NEW_INVOICES:
        client_name = inv['client'].strip().lower()
        
        if client_name in all_existing_clients:
            print(f"⏭️ Skipping {inv['client']} - already exists in sheets.")
            continue
            
        print(f"➕ New client found: {inv['client']} ({inv['type']})")
        
        target_ws = prepaids_ws if inv['type'] == 'prepaid' else monthly_ws
        
        append_to_sheet(target_ws, inv, next_agent)
        
        # Add to our known list so we don't duplicate within the same run
        all_existing_clients.add(client_name)
        
        # Toggle agent for the next client
        next_agent = "Sulejman" if next_agent == "Katty" else "Katty"
        
    print("\n🎉 Done updating sheets!")

if __name__ == "__main__":
    # Test sheet ID provided by user
    TEST_SHEET_URL = "https://docs.google.com/spreadsheets/d/191g9fIbjKi-r2hA_5PxbyVfVN3rx7e5rFlfEGH5NfDM/edit"
    main(TEST_SHEET_URL)
