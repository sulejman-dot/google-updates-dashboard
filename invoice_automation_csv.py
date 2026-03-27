import gspread
from oauth2client.service_account import ServiceAccountCredentials
import csv
import sys
import os
from datetime import datetime

# Auth and setup
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'service_account.json'

def get_sheet_client():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    client = gspread.authorize(creds)
    return client

def get_existing_clients(worksheet):
    records = worksheet.get_all_records()
    clients = [str(r.get('Client', '')).strip().lower() for r in records if r.get('Client')]
    return clients

def get_last_assigned_agent(prepaids_ws, monthly_ws):
    agents = []
    for ws in [prepaids_ws, monthly_ws]:
        records = ws.get_all_records()
        for r in records:
            agent = str(r.get('Agent', '')).strip()
            if agent in ['Sulejman', 'Katty']: 
                agents.append(agent)
                
    last_agent = None
    for agent in reversed(agents):
        if agent in ['Sulejman', 'Katty']:
            last_agent = agent
            break
            
    return last_agent

def append_to_sheet(ws, client_name, payment_term, date_issued, agent):
    row_data = [
        client_name,
        payment_term,
        date_issued,
        agent,
        "", "Ongoing...", "", "", ""
    ]
    ws.append_row(row_data)
    print(f"✅ Added {client_name} to {ws.title} and assigned to {agent}")

def get_transaction_errors(transactions_csv):
    """Returns a dict mapping Invoice Number to the latest failure Error Text"""
    errors = {}
    if not os.path.exists(transactions_csv):
        return errors
        
    with open(transactions_csv, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            inv_num = row.get('Invoice Number', '').strip()
            status = row.get('Status', '').strip().lower()
            if status == 'failure':
                error_txt = row.get('Error Text', '').strip()
                if error_txt:
                    errors[inv_num] = error_txt
    return errors

def get_card_statuses(cards_csv):
    """Returns a dict mapping Customer Id to the card Status (e.g. 'Expired', 'Valid')"""
    cards = {}
    if not os.path.exists(cards_csv):
        return cards
        
    with open(cards_csv, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get('Customer Id', '').strip()
            status = row.get('Status', '').strip()
            if status:
                cards[cid] = status
    return cards

def format_date_suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def generate_draft_email(first_name, date_issued, amount_str, error_reason, inv_type, card_status):
    if not first_name:
        first_name = "there"
        
    try:
        dt = datetime.strptime(date_issued, "%d-%b-%Y")
        formatted_date = dt.strftime(f"%B {dt.day}{format_date_suffix(dt.day)}")
    except:
        formatted_date = date_issued

    # Contextual wording based on card status and error reason
    body = ""
    
    if str(card_status).lower() == 'expired':
        body = f"""I’m contacting you from the SEOmonitor Customer Service team regarding your {inv_type.lower()} invoice of {amount_str}, scheduled for {formatted_date}. Unfortunately, the payment attempt was declined due to an “Expired card” notification.

This typically means the card on file is no longer valid. Please update your payment method so we can process the invoice successfully."""

    elif error_reason:
        # Valid card but transaction failed
        body = f"""I’m contacting you from the SEOmonitor Customer Service team regarding your {inv_type.lower()} invoice of {amount_str}, scheduled for {formatted_date}. Unfortunately, the payment attempt was declined due to a “{error_reason}” notification.

Please review your payment method or ensure sufficient funds are available so we can process the invoice successfully."""

    else:
        # No card or no transaction error
        body = f"""I’m contacting you from the SEOmonitor Customer Service team regarding your {inv_type.lower()} invoice of {amount_str}, scheduled for {formatted_date}. The payment is currently pending as we haven't received it yet.

Please arrange for the payment to be completed as soon as possible so we can process the invoice successfully."""

    draft = f"""Hi {first_name},

I hope you’re well.

{body}

If you need any assistance updating your billing details or retrying the payment, please let me know — I’ll be happy to help.

Best,
Sulejman"""
    return draft

def append_email_draft(sheet, client_name, draft, agent):
    try:
        ws = sheet.worksheet("emails")
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title="emails", rows="100", cols="4")
        ws.append_row(["Date Added", "Client", "Agent", "Draft Email"])
        
    ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), client_name, agent, draft])
    print(f"📧 Added draft email for {client_name} to 'emails' tab.")

def read_invoices_csv(invoices_csv, tx_errors, card_statuses):
    unpaid_invoices = []
    
    with open(invoices_csv, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = row.get('Status', '').strip().lower()
            if status in ['payment due', 'not paid']:
                first_name = row.get('Customer First Name', '').strip()
                last_name = row.get('Customer Last Name', '').strip()
                company = row.get('Customer Company', '').strip()
                cid = row.get('Customer Id', '').strip()
                
                if company:
                    client_name = company
                else:
                    client_name = f"{first_name} {last_name}".strip()
                
                term_days = row.get('Net Term Days', '30').strip()
                if not term_days: term_days = "30"
                payment_term = f"NET{term_days}"
                
                full_date = row.get('Invoice Date', '').strip()
                date_issued = full_date.split(' ')[0] if full_date else ""
                
                is_recurring = str(row.get('Recurring', 'false')).strip().lower() == 'true'
                invoice_type = "monthly" if is_recurring else "prepaid"
                
                inv_num = row.get('Invoice Number', '').strip()
                raw_amount = row.get('Amount', '')
                if raw_amount.endswith('.00'):
                    raw_amount = raw_amount[:-3]
                    
                currency = row.get('Currency', 'EUR')
                sym = "€" if currency == "EUR" else ("$" if currency == "USD" else ("£" if currency == "GBP" else currency + " "))
                formatted_amount = f"{sym}{raw_amount}"
                
                error_reason = tx_errors.get(inv_num, "")
                c_status = card_statuses.get(cid, "")
                
                if not client_name:
                    continue
                    
                unpaid_invoices.append({
                    'client': client_name,
                    'first_name': first_name,
                    'payment_term': payment_term,
                    'date_issued': date_issued,
                    'type': invoice_type,
                    'amount_str': formatted_amount,
                    'error_reason': error_reason,
                    'card_status': c_status
                })
                
def main(sheet_url, base_dir):
    invoices_csv = os.path.join(base_dir, "Invoices.csv")
    transactions_csv = os.path.join(base_dir, "Transactions.csv")
    cards_csv = os.path.join(base_dir, "Cards.csv")
    
    if not os.path.exists(invoices_csv):
        if base_dir.endswith("Invoices.csv"):
            invoices_csv = base_dir
            transactions_csv = os.path.join(os.path.dirname(base_dir), "Transactions.csv")
            cards_csv = os.path.join(os.path.dirname(base_dir), "Cards.csv")
        else:
            print(f"❌ Could not find Invoices.csv in: {base_dir}")
            return None
            
    print(f"📂 Reading data from: {os.path.dirname(invoices_csv)}...")
    tx_errors = get_transaction_errors(transactions_csv)
    card_statuses = get_card_statuses(cards_csv)
    unpaid_invoices = read_invoices_csv(invoices_csv, tx_errors, card_statuses)
    
    print(f"Found {len(unpaid_invoices)} Unpaid / Payment Due invoices.")
    
    if not unpaid_invoices:
        print("🎉 No unpaid invoices found to process!")
        return {'Sulejman': 0, 'Katty': 0}

    print("🔄 Connecting to Google Sheets...")
    client = get_sheet_client()
    sheet = client.open_by_url(sheet_url)
    
    try:
        prepaids_ws = sheet.worksheet("Prepaids")
        monthly_ws = sheet.worksheet("Monthly unpaid")
    except gspread.exceptions.WorksheetNotFound as e:
        print(f"❌ Could not find the required tabs: {e}")
        return None

    print("📊 Fetching existing clients from Sheets...")
    existing_prepaid = get_existing_clients(prepaids_ws)
    existing_monthly = get_existing_clients(monthly_ws)
    
    all_existing_clients = set(existing_prepaid + existing_monthly)
    
    last_agent = get_last_assigned_agent(prepaids_ws, monthly_ws)
    next_agent = "Katty" if last_agent == "Sulejman" else "Sulejman"
    print(f"ℹ️ Round-Robin starting with: {next_agent}")

    added_count = 0
    assigned_counts = {'Sulejman': 0, 'Katty': 0}
    
    for inv in unpaid_invoices:
        client_name_lower = inv['client'].strip().lower()
        if client_name_lower in all_existing_clients:
            continue
            
        print(f"➕ New client found: {inv['client']} ({inv['type'].title()})")
        target_ws = prepaids_ws if inv['type'] == 'prepaid' else monthly_ws
        
        append_to_sheet(target_ws, inv['client'], inv['payment_term'], inv['date_issued'], next_agent)
        
        # Only draft emails for Sulejman
        if next_agent == "Sulejman":
            draft = generate_draft_email(
                inv['first_name'], 
                inv['date_issued'], 
                inv['amount_str'], 
                inv['error_reason'], 
                inv['type'],
                inv['card_status']
            )
            append_email_draft(sheet, inv['client'], draft, next_agent)
        
        all_existing_clients.add(client_name_lower)
        added_count += 1
        assigned_counts[next_agent] += 1
        
        next_agent = "Sulejman" if next_agent == "Katty" else "Katty"
        
    print(f"\n🎉 Done! Added {added_count} new entries to the tracker.")
    return assigned_countsne! Added {added_count} new entries to the tracker.")

if __name__ == "__main__":
    TEST_SHEET_URL = "https://docs.google.com/spreadsheets/d/191g9fIbjKi-r2hA_5PxbyVfVN3rx7e5rFlfEGH5NfDM/edit"
    arg_dir = sys.argv[1] if len(sys.argv) > 1 else "/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Sulejman Workspace/tmp_invoices"
    main(TEST_SHEET_URL, arg_dir)
