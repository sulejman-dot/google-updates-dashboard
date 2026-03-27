# Workflow: Shareable Activity Report System

## Purpose
A dynamic system to generate professional activity reports with automated signing.

## Phase 1: One-Time Onboarding
The first time anyone runs the generator, it will perform a "First Time Setup":
1.  **Run the script:** `python3 generate_report.py`
2.  **Provide Details:** Enter **Full Name**, **Hourly Rate (EUR)**, and **Internal Contract Hours** (e.g., 140). 
    - *Note: The hours you enter here will be automatically distributed across activity categories in your report.*
3.  **Signature Path (Optional):** Provide the full path to your `signature.png`. If skipped, the report will show a standard signature line.
4.  **Save:** The system creates `config.json` and remembers these details forever.

## Phase 2: Monthly Generation
For every future report, the system only asks for the variables that change each month:
1.  **Ask Month:** (e.g., "February 2026")
2.  **Ask Invoice Number:** (e.g., "INV-101")
3.  **Generate:** The script calculates totals and embeds your signature automatically.

## Requirements
- **signature.png:** A clean, cropped PNG of your signature.
- **Python 3:** Required to run the generator.

## Technical Implementation
Copy the following code into a file named `generate_report.py`:

```python
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

    rtf = r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Times New Roman;}}\f0\fs24 "
    rtf += r"{\b\fs28 Acceptance and Activity Report}\par "
    rtf += f"{{\\fs24 {month_year}/Invoice no. {invoice_no}}}\\par\\par "
    rtf += f"By this Protocol, the Beneficiary declares that they accept the agreed services in accordance with the terms stipulated in the Freelance Contract/{{config['contract_date']}}. In accordance with the contractual provisions, please find attached the activity report\\par\\par "
    rtf += r"The value of the services provided for the relevant period is detailed below.\par\par "

    def cell_with_borders(text, width=2500, align=r"\ql", bold=False, italic=False):
        borders = r"\clbrdrt\brdrs\brdrw10 \clbrdrl\brdrs\brdrw10 \clbrdrb\brdrs\brdrw10 \clbrdrr\brdrs\brdrw10 "
        style = ""
        if bold: style += r"\b "
        if italic: style += r"\i "
        return f"{borders}\cellx{width} " + (r"{\trowd \trgaph108 " if width == 0 else "") + f"{align} {style}{text}" + (r"\b0 " if bold else "") + (r"\i0 " if italic else "") + r"\cell "

    w1, w2, w3, w4 = 5000, 6500, 8000, 9500
    rtf += r"\trowd\trgaph108"
    rtf += cell_with_borders("Description of services", w1, bold=True)
    rtf += cell_with_borders("Qty/No. of Hours", w2, align=r"\qc", bold=True)
    rtf += cell_with_borders("Unit Price", w3, align=r"\qc", bold=True)
    rtf += cell_with_borders("Value", w4, align=r"\qc", bold=True)
    rtf += r"\row "

    fee = config["fee_rate"]
    total = config["contract_hours"]
    h1, h2, h3, h4 = int(total*0.25), int(total*0.20), int(total*0.20), int(total*0.20)
    h5 = total - (h1+h2+h3+h4)
    
    rows = [
        (r"Financial Planning & Operations\par\fs20 - Q1 2026 budget development and cashflow analysis\par - Management of commission reports and operational payments\fs24 ", f"{h1}", f"{fee} EUR", f"{h1*fee} EUR"),
        (r"Operational Strategy & Automation\par\fs20 - MRR reporting flow optimization (Chargebee)\par - Analysis and implementation of API automation solutions\fs24 ", f"{h2}", f"{fee} EUR", f"{h2*fee} EUR"),
        (r"Administrative & Legal Compliance\par\fs20 - Vendor contract management and legal checks\par - Legislative analysis for sublease contracts (ANAF/B2B)\fs24 ", f"{h3}", f"{fee} EUR", f"{h3*fee} EUR"),
        (r"Office & Fleet Management\par\fs20 - Support fleet administration and insurance\par - Office logistics and maintenance management\fs24 ", f"{h4}", f"{fee} EUR", f"{h4*fee} EUR"),
        (r"Strategic Review & Team Alignment\par\fs20 - Participation in weekly management reviews\par - Cross-departmental alignment for operational processes\fs24 ", f"{h5}", f"{fee} EUR", f"{h5*fee} EUR")
    ]

    for desc, qty, price, val in rows:
        rtf += r"\trowd\trgaph108"
        rtf += cell_with_borders(desc, w1)
        rtf += cell_with_borders(qty, w2, align=r"\qc")
        rtf += cell_with_borders(price, w3, align=r"\qc")
        rtf += cell_with_borders(val, w4, align=r"\qc")
        rtf += r"\row "

    rtf += r"\trowd\trgaph108"
    rtf += cell_with_borders("Total", w1, align=r"\qr", bold=True)
    rtf += cell_with_borders(f"{total}", w2, align=r"\qc", bold=True)
    rtf += cell_with_borders("....", w3, align=r"\qc", bold=True)
    rtf += cell_with_borders(f"{total*fee} EUR", w4, align=r"\qc", bold=True)
    rtf += r"\row "

    rtf += r"\par\par\par \trowd\trgaph108"
    rtf += f"\cellx4750 \\b Provider\\b0 \cell \cellx9500 \\b Beneficiary\\b0 \cell \\row "
    rtf += r"\trowd\trgaph108"
    rtf += f"\cellx4750 Name: {config['name']}\cell \cellx9500 Name: Seomonitor Software SRL\cell \\row "
    rtf += r"\trowd\trgaph108"
    
    sig_path = config.get("signature_path", "")
    if sig_path and os.path.exists(sig_path):
        with open(sig_path, "rb") as f:
            hex_data = binascii.hexlify(f.read()).decode('utf-8')
        rtf += f"\cellx4750 Signature:\par {{\pict\pngblip\picwgoal2640\pichgoal705 {hex_data}}}\cell "
    else:
        rtf += r"\cellx4750 Signature:\par _______________________\cell "
    
    rtf += r"\cellx9500 Signature:\par\par _______________________\cell \row }"
    
    with open(output_path, "w") as f:
        f.write(rtf)

if __name__ == "__main__":
    config = get_config()
    month_year = input("Enter Month and Year (e.g., January 2026): ")
    invoice_no = input("Enter Invoice Number: ")
    
    # Simple filename generation
    filename = f"Activity_Report_{month_year.replace(' ', '_')}.rtf"
    generate_rtf_report(filename, month_year, invoice_no)
    print(f"\nSuccess! Report generated as: {filename}")
```

## Output
A professional `.rtf` file in the `Collected Context/Activity Reports` folder with perfect table lines and signature alignment.
