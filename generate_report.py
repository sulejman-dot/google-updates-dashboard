
import os
import json
import binascii

CONFIG_FILE = "config.json"

def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    
    # Onboarding for first-time use
    print("--- FIRST TIME SETUP ---")
    config = {}
    config["name"] = input("Enter your Full Name: ")
    config["fee_rate"] = float(input("Enter your Hourly Rate (EUR): "))
    config["contract_hours"] = int(input("Enter total monthly Contract Hours (e.g., 140): "))
    config["contract_date"] = input("Enter Contract Start Date (e.g., 03.02.2025): ")
    config["signature_path"] = input("Enter path to signature PNG (or leave blank to skip): ").strip().replace("'", "").replace("\"", "")
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    print(f"Setup complete! Config saved to {CONFIG_FILE}\n")
    return config

def generate_rtf_report(output_path, month_year, invoice_no):
    config = get_config()
    
    if not invoice_no: invoice_no = "[INSERT INVOICE NO]"

    # RTF Header and Font Table
    rtf = r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Times New Roman;}}\f0\fs24 "
    
    # Title and Header
    rtf += r"{\b\fs28 Acceptance and Activity Report}\par "
    rtf += f"{{\\fs24 {month_year}/Invoice no. {invoice_no}}}\\par\\par "
    
    # Body Text with exact contract date
    rtf += f"By this Protocol, the Beneficiary declares that they accept the agreed services in accordance with the terms stipulated in the Freelance Contract/{config['contract_date']}. In accordance with the contractual provisions, please find attached the activity report\\par\\par "
    rtf += r"The value of the services provided for the relevant period is detailed below.\par\par "
    
    # Table Border Definition Helper
    def cell_with_borders(text, width=2500, align=r"\ql", bold=False, italic=False):
        borders = r"\clbrdrt\brdrs\brdrw10 \clbrdrl\brdrs\brdrw10 \clbrdrb\brdrs\brdrw10 \clbrdrr\brdrs\brdrw10 "
        style = ""
        if bold: style += r"\b "
        if italic: style += r"\i "
        return f"{borders}\cellx{width} " + (r"{\trowd \trgaph108 " if width == 0 else "") + f"{align} {style}{text}" + (r"\b0 " if bold else "") + (r"\i0 " if italic else "") + r"\cell "

    # Define Column Widths
    w1 = 5000  # Description
    w2 = 6500  # Qty
    w3 = 8000  # Price
    w4 = 9500  # Value

    # Table Header Row
    rtf += r"\trowd\trgaph108"
    rtf += cell_with_borders("Description of services", w1, bold=True)
    rtf += cell_with_borders("Qty/No. of Hours", w2, align=r"\qc", bold=True)
    rtf += cell_with_borders("Unit Price", w3, align=r"\qc", bold=True)
    rtf += cell_with_borders("Value", w4, align=r"\qc", bold=True)
    rtf += r"\row "

    # Data Rows
    fee = config["fee_rate"]
    total_hours = config["contract_hours"]
    
    h1 = int(total_hours * 0.25)
    h2 = int(total_hours * 0.20)
    h3 = int(total_hours * 0.20)
    h4 = int(total_hours * 0.20)
    h5 = total_hours - (h1 + h2 + h3 + h4)
    
    rows = [
        (r"Financial Planning & Operations\par\fs20 - Q1 2026 budget development and cashflow analysis\par - Management of commission reports and operational payments\fs24 ", f"{h1}", f"{fee} EUR", f"{h1*fee} EUR"),
        (r"Operational Strategy & Automation\par\fs20 - MRR reporting flow optimization (Chargebee)\par - Analysis and implementation of API automation solutions\fs24 ", f"{h2}", f"{fee} EUR", f"{h2*fee} EUR"),
        (r"Administrative & Legal Compliance\par\fs20 - Vendor contract management and legal checks\par - Legislative analysis for sublease contracts (ANAF/B2B)\fs24 ", f"{h3}", f"{fee} EUR", f"{h3*fee} EUR"),
        (r"Office & Fleet Management\par\fs20 - Support fleet administration and insurance\par - Office logistics and maintenance management\fs24 ", f"{h4}", f"{fee} EUR", f"{h4*fee} EUR"),
        (r"Strategic Review & Team Alignment\par\fs20 - Participation in weekly management reviews\par - Cross-departmental alignment for operational processes\fs24 ", f"{h5}", f"{fee} EUR", f"{h5*fee} EUR"),
        ("", "", "", ""),
        ("", "", "", "")
    ]

    for desc, qty, price, val in rows:
        rtf += r"\trowd\trgaph108"
        rtf += cell_with_borders(desc, w1)
        rtf += cell_with_borders(qty, w2, align=r"\qc")
        rtf += cell_with_borders(price, w3, align=r"\qc")
        rtf += cell_with_borders(val, w4, align=r"\qc")
        rtf += r"\row "

    # Total Row
    rtf += r"\trowd\trgaph108"
    rtf += cell_with_borders("Total", w1, align=r"\qr", bold=True)
    rtf += cell_with_borders(f"{total_hours}", w2, align=r"\qc", bold=True)
    rtf += cell_with_borders("....", w3, align=r"\qc", bold=True)
    rtf += cell_with_borders(f"{total_hours*fee} EUR", w4, align=r"\qc", bold=True)
    rtf += r"\row "

    # Signature Block
    rtf += r"\par\par\par "
    rtf += r"\trowd\trgaph108"
    def sig_cell(text, width, bold=False):
        b_on = r"\b " if bold else ""
        b_off = r"\b0 " if bold else ""
        return f"\cellx{width} {b_on}{text}{b_off}\cell "

    w_sig = 4750
    rtf += sig_cell("Provider", w_sig, bold=True)
    rtf += sig_cell("Beneficiary", 9500, bold=True)
    rtf += r"\row "
    
    rtf += r"\trowd\trgaph108"
    rtf += sig_cell(f"Name: {config['name']}", w_sig)
    rtf += sig_cell("Name: Seomonitor Software SRL", 9500)
    rtf += r"\row "
    
    # Signature row
    rtf += r"\trowd\trgaph108"
    sig_content = "Signature:"
    sig_path = config.get("signature_path", "")
    if sig_path and os.path.exists(sig_path):
        with open(sig_path, "rb") as f:
            hex_data = binascii.hexlify(f.read()).decode('utf-8')
        rtf += sig_cell(sig_content + r"\par {\pict\pngblip\picwgoal2640\pichgoal705 " + hex_data + r"}", w_sig)
    else:
        rtf += sig_cell(sig_content + r"\par _______________________", w_sig)
    
    rtf += sig_cell(r"Signature:\par\par _______________________", 9500)
    rtf += r"\row "

    rtf += r"}"
    
    with open(output_path, "w") as f:
        f.write(rtf)

if __name__ == "__main__":
    config = get_config()
    print("--- MONTHLY REPORT DETAILS ---")
    month_year = input("Enter Month and Year (e.g., January 2026): ")
    invoice_no = input("Enter Invoice Number (or leave blank if unknown): ")
    
    # Format filename
    months = {
        "january": "01", "ianuarie": "01",
        "february": "02", "februarie": "02",
        "march": "03", "martie": "03",
        "april": "04", "aprilie": "04",
        "may": "05", "mai": "05",
        "june": "06", "iunie": "06", 
        "july": "07", "iulie": "07",
        "august": "08", "august": "08",
        "september": "09", "septembrie": "09",
        "october": "10", "octombrie": "10",
        "november": "11", "noiembrie": "11",
        "december": "12", "decembrie": "12"
    }
    parts = month_year.lower().split()
    month_code = "00"
    year_code = "2026"
    for p in parts:
        if p in months: month_code = months[p]
        if p.isdigit() and len(p) == 4: year_code = p
    
    first_name = config.get("name", "User").split()[0]
    filename = f"{year_code}-{month_code}_Raport_Activitate_{first_name}.rtf"
    reports_dir = os.path.join(os.getcwd(), "Collected Context/Activity Reports")
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.join(reports_dir, filename)
    
    generate_rtf_report(path, month_year, invoice_no)
    print(f"\nSuccess! Report generated at: {path}")
