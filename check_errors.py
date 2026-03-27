import csv

txs = {}
with open('tmp_invoices/Transactions.csv', 'r') as f:
    for row in csv.DictReader(f):
        if row.get('Status').lower() == 'failure':
            txs[row.get('Invoice Number')] = row.get('Error Text')

cards = {}
with open('tmp_invoices/Cards.csv', 'r') as f:
    for row in csv.DictReader(f):
        cards[row.get('Customer Id')] = row.get('Status')

invoices = []
with open('tmp_invoices/Invoices.csv', 'r') as f:
    for row in csv.DictReader(f):
        if row.get('Status').lower() in ['payment due', 'not paid']:
            invoices.append(row)

for inv in invoices:
    num = inv['Invoice Number']
    cid = inv['Customer Id']
    company = inv['Customer Company'] or f"{inv['Customer First Name']} {inv['Customer Last Name']}"
    err = txs.get(num, '')
    c_status = cards.get(cid, 'No Card')
    print(f"[{num}] {company} | TX Error: '{err}' | Card: {c_status}")
