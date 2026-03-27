import os
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load env variables
load_dotenv()

CHARGEBEE_SITE = os.getenv("CHARGEBEE_SITE")
CHARGEBEE_API_KEY = os.getenv("CHARGEBEE_API_KEY")

class MockChargebeeClient:
    """Mock client for development until API keys are available"""
    def list_invoices(self, status="not_paid"):
        print("🧪 MOCK MODE: Fetching mock invoices...")
        return [
            {
                "id": "INV-001",
                "customer_email": "clientA@example.com",
                "amount": 1000,
                "date": (datetime.now() - timedelta(days=2)).timestamp(),
                "status": "payment_failed",
                "failure_reason": "card_expired"
            },
            {
                "id": "INV-002",
                "customer_email": "ghost@example.com",
                "amount": 500,
                "date": (datetime.now() - timedelta(days=20)).timestamp(),
                "status": "payment_failed",
                "failure_reason": None # Unknown/No reason
            },
             {
                "id": "INV-003",
                "customer_email": "new_fail@example.com",
                "amount": 250,
                "date": (datetime.now() - timedelta(days=4)).timestamp(),
                "status": "payment_failed",
                "failure_reason": "insufficient_funds"
            }
        ]

def get_client(dry_run=False):
    if not dry_run and CHARGEBEE_API_KEY and CHARGEBEE_SITE:
        # TODO: Return real client when keys exist
        # import chargebee
        # chargebee.configure(CHARGEBEE_API_KEY, CHARGEBEE_SITE)
        # return chargebee.Invoice
        pass
    
    # Fallback to mock
    if not dry_run:
        print("⚠️  Warning: Using Mock Client (No API Keys found or not implemented)")
    return MockChargebeeClient()

def analyze_scenario(invoice, today_ts):
    """
    Determines the Chase Path (A, B, or C) based on invoice data.
    """
    failure_reason = invoice.get('failure_reason')
    inv_date_ts = invoice.get('date')
    days_overdue = (today_ts - inv_date_ts) / (24 * 3600)
    
    # Filter valid failure reasons for Path A (Technical)
    tech_reasons = ['card_expired', 'insufficient_funds', 'cannot_authorize']
    
    scenario = "Unknown"
    tone = "Neutral"
    
    if failure_reason in tech_reasons:
        scenario = "Path A: The 'Oops' (Technical)"
        tone = "Friendly/Helpful"
    elif days_overdue > 14:
        scenario = "Path B: The 'Ghost' (Non-Responsive)"
        tone = "Firm"
    elif days_overdue < 7:
        scenario = "Path A/C: Soft Nudge"
        tone = "Gentle"
        
    return scenario, tone, days_overdue

def generate_draft(invoice, scenario, tone):
    """
    Generates the email draft content.
    """
    amount = f"${invoice['amount']}"
    date_str = datetime.fromtimestamp(invoice['date']).strftime('%Y-%m-%d')
    reason = invoice.get('failure_reason') or "Unknown Error"
    
    draft = f"""
    --------------------------------------------------
    TO: {invoice['customer_email']}
    SUBJECT: Payment Update for Invoice #{invoice['id']}
    
    Hi there,
    
    [TONE: {tone}]
    """
    
    if "Technical" in scenario:
        draft += f"\nWe noticed a hiccup with the payment for Invoice #{invoice['id']} ({amount}).\n"
        draft += f"The bank mentioned: '{reason}'.\n"
        draft += "Could you please check your card details? Here is the link: [LINK]"
        
    elif "Ghost" in scenario:
        draft += f"\nWe are writing regarding the overdue invoice #{invoice['id']} from {date_str}.\n"
        draft += f"We have not received payment or a response. Please settle this immediately to avoid service interruption."
        
    else:
        draft += f"\nJust a quick nudge regarding Invoice #{invoice['id']} for {amount}.\n"
        draft += "Please let us know if there is an issue fulfilling this."
        
    draft += "\n\nBest,\nSulejman"
    draft += "\n--------------------------------------------------"
    return draft

def main():
    parser = argparse.ArgumentParser(description="Auto-Chase Invoices")
    parser.add_argument("--dry-run", action="store_true", help="Use mock data")
    args = parser.parse_args()
    
    client = get_client(dry_run=args.dry_run)
    invoices = client.list_invoices()
    
    print(f"Found {len(invoices)} candidate invoices.\n")
    
    today_ts = datetime.now().timestamp()
    
    for inv in invoices:
        scenario, tone, days = analyze_scenario(inv, today_ts)
        print(f"🧾 Invoice {inv['id']} | {inv['customer_email']}")
        print(f"   Amount: ${inv['amount']} | Overdue: {int(days)} days")
        print(f"   Reason: {inv.get('failure_reason')}")
        print(f"   👉 Strategy: {scenario}")
        
        draft = generate_draft(inv, scenario, tone)
        print(draft)
        print("\n")

if __name__ == "__main__":
    main()
