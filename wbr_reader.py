import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Sheet ID extracted from URL
SHEET_ID = "161qbyJ5nQsgDEaudZ5O1C4zldUIBbeDiYMYyCgldG40"

def get_wbr_summary(mock=True):
    """
    Reads the WBR Google Sheet and returns a summary.
    For now, returns mock data until Google credentials are set up.
    """
    if mock:
        return {
            "summary": "📊 WBR Summary (Mock Data)",
            "sheets": [
                {"name": "Overview", "key_metric": "Total Tasks: 42"},
                {"name": "Product", "key_metric": "Completed: 15/20"},
                {"name": "Maintenance", "key_metric": "Open: 8"},
                {"name": "Support", "key_metric": "Avg Response: 2.3h"},
                {"name": "Metrics", "key_metric": "NPS: 45"}
            ]
        }
    
    # Real implementation (requires Google Service Account JSON)
    try:
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        # This will need a service account JSON file
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'google_credentials.json', scope)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(SHEET_ID)
        
        # Read all worksheets
        worksheets = sheet.worksheets()
        summary = {
            "summary": f"📊 WBR Summary ({len(worksheets)} sheets)",
            "sheets": []
        }
        
        for ws in worksheets:
            # Get first few rows to extract key metrics
            data = ws.get_all_values()[:5]  # First 5 rows
            summary["sheets"].append({
                "name": ws.title,
                "key_metric": f"Rows: {len(data)}"
            })
        
        return summary
        
    except Exception as e:
        return {
            "summary": f"❌ Error reading sheet: {str(e)}",
            "sheets": []
        }

if __name__ == "__main__":
    # Test with mock data
    result = get_wbr_summary(mock=True)
    print(result)
