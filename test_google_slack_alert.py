from google_update_monitor import send_slack_alert
print("Sending test Slack Alert (Official Google Dashboard)...")
send_slack_alert("Google Core Update", "AVAILABLE", "HIGH", "https://status.search.google.com/incidents.json", "This is a test notification for the Google Core Update. For more details see <https://developers.google.com/search/docs/appearance/spam-updates>.", True, "Google Status Dashboard")

print("Sending test Slack Alert (Community News)...")
send_slack_alert("Unpublished Volatility Detected", "Community Report", "Info/Unconfirmed", "https://www.seroundtable.com", "SEO webmasters are reporting huge SERP volatility today.", True, "Search Engine Roundtable")

print("Test complete.")
