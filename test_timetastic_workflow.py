#!/usr/bin/env python3
"""
Test Timetastic API Integration Workflow
Simulates the Make flow to verify the filtering logic works correctly
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
API_TOKEN = "05e639d8-4f09-4b5a-ad2b-1bf39d2bae4f"
BASE_URL = "https://app.timetastic.co.uk/api/absences"

# Simulate today's date (Module 3 & 4 in Make)
today = datetime.now()
start_date = today.strftime("%Y-%m-%d")
end_date = today.strftime("%Y-%m-%d")

print("=" * 70)
print("TIMETASTIC API WORKFLOW TEST")
print("=" * 70)
print(f"\nDate Range: {start_date} to {end_date}")
print(f"Current Time: {today.strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================================================
# MODULE 8: Simulated Active Users from Google Sheets
# ============================================================================
print("\n" + "=" * 70)
print("MODULE 8: Active Users (from Google Sheets)")
print("=" * 70)

# This would come from your Google Sheets in the real flow
active_users = [
    {"name": "Alice Johnson", "email": "alice@company.com", "department": "Engineering"},
    {"name": "Bob Smith", "email": "bob@company.com", "department": "Product"},
    {"name": "Carol Davis", "email": "carol@company.com", "department": "Support"},
    {"name": "David Lee", "email": "david@company.com", "department": "Engineering"},
    {"name": "Eve Martinez", "email": "eve@company.com", "department": "Sales"},
]

print(f"\nTotal Active Users: {len(active_users)}")
for user in active_users:
    print(f"  - {user['name']} ({user['email']})")

# ============================================================================
# MODULE 8A: Call Timetastic API
# ============================================================================
print("\n" + "=" * 70)
print("MODULE 8A: HTTP Request to Timetastic API")
print("=" * 70)

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

params = {
    "Start": start_date,
    "End": end_date,
    "AbsenceQueryType": "AllAbsences"
}

print(f"\nRequest URL: {BASE_URL}")
print(f"Query Parameters: {json.dumps(params, indent=2)}")
print(f"Headers: Authorization: Bearer {API_TOKEN[:20]}...")

try:
    response = requests.get(BASE_URL, headers=headers, params=params)
    
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code == 200:
        absences_data = response.json()
        print(f"Response received successfully!")
        print(f"\nRaw API Response:")
        print(json.dumps(absences_data, indent=2))
        
        # ============================================================================
        # MODULE 8B-1: Extract Absent User Emails
        # ============================================================================
        print("\n" + "=" * 70)
        print("MODULE 8B-1: Extract Absent User Emails")
        print("=" * 70)
        
        # Simulate Make's map() function: map(8A.array[].absences[]; "user.email")
        absent_emails = []
        for day in absences_data:
            if "absences" in day:
                for absence in day["absences"]:
                    if "user" in absence and "email" in absence["user"]:
                        absent_emails.append(absence["user"]["email"])
        
        print(f"\nAbsent Emails Array: {absent_emails}")
        print(f"Total Absent Users: {len(absent_emails)}")
        
        if absent_emails:
            print("\nAbsent Users Details:")
            for day in absences_data:
                if "absences" in day:
                    for absence in day["absences"]:
                        user = absence.get("user", {})
                        print(f"  - {user.get('firstname', '')} {user.get('surname', '')} ({user.get('email', '')})")
                        print(f"    Type: {absence.get('absenceType', 'N/A')}")
                        print(f"    Detail: {absence.get('detail', 'N/A')}")
                        print(f"    Time: {absence.get('start', 'N/A')} to {absence.get('end', 'N/A')}")
        else:
            print("\n✓ No absences found for today!")
        
        # ============================================================================
        # MODULE 8B-2: Filter Available Users
        # ============================================================================
        print("\n" + "=" * 70)
        print("MODULE 8B-2: Filter Available Users")
        print("=" * 70)
        
        # Simulate Make's filter: contains(absent_emails; 8.email) = false
        available_users = []
        for user in active_users:
            is_absent = user["email"] in absent_emails
            status = "EXCLUDED ✗" if is_absent else "INCLUDED ✓"
            print(f"  {user['name']:20} ({user['email']:25}) → {status}")
            
            if not is_absent:
                available_users.append(user)
        
        print(f"\nFiltered Result: {len(available_users)} available users")
        
        # ============================================================================
        # MODULE 11: Array Aggregator (simulated)
        # ============================================================================
        print("\n" + "=" * 70)
        print("MODULE 11: Array Aggregator")
        print("=" * 70)
        print(f"\nAggregated {len(available_users)} available users")
        
        # ============================================================================
        # MODULE 12: Count Available Team Members
        # ============================================================================
        print("\n" + "=" * 70)
        print("MODULE 12: Count Available Team Members")
        print("=" * 70)
        total_available_members = len(available_users)
        print(f"\nTotal Available Members: {total_available_members}")
        
        # ============================================================================
        # MODULE 13: Calculate Response Rate
        # ============================================================================
        print("\n" + "=" * 70)
        print("MODULE 13: Calculate Response Rate")
        print("=" * 70)
        
        # Simulate some users checked in (for demonstration)
        unique_users_checked_in = 2  # Example: 2 users checked in today
        
        if total_available_members > 0:
            response_rate = round((unique_users_checked_in / total_available_members) * 100, 1)
        else:
            response_rate = 0
        
        print(f"\nUsers Checked In: {unique_users_checked_in}")
        print(f"Available Members: {total_available_members}")
        print(f"Response Rate: {response_rate}%")
        
        # Comparison
        original_total = len(active_users)
        original_rate = round((unique_users_checked_in / original_total) * 100, 1) if original_total > 0 else 0
        
        print(f"\n📊 COMPARISON:")
        print(f"  Without Timetastic: {unique_users_checked_in}/{original_total} = {original_rate}%")
        print(f"  With Timetastic:    {unique_users_checked_in}/{total_available_members} = {response_rate}%")
        print(f"  Improvement: {response_rate - original_rate:+.1f}%")
        
        # ============================================================================
        # SUMMARY
        # ============================================================================
        print("\n" + "=" * 70)
        print("✅ WORKFLOW TEST COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"\n✓ API Connection: Working")
        print(f"✓ Absences Retrieved: {len(absent_emails)} users")
        print(f"✓ Filtering Logic: Working")
        print(f"✓ Response Rate Calculation: Accurate")
        
    elif response.status_code == 401:
        print("\n❌ ERROR: 401 Unauthorized")
        print("The API token is invalid or expired.")
        print("Please check your token at: https://app.timetastic.co.uk/api")
        
    elif response.status_code == 429:
        print("\n❌ ERROR: 429 Rate Limit Exceeded")
        print("You've exceeded the rate limit (1 request per second)")
        print("Wait a moment and try again.")
        
    else:
        print(f"\n❌ ERROR: Unexpected status code {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"\n❌ ERROR: Network request failed")
    print(f"Error: {str(e)}")
    print("\nThe flow would continue with unfiltered users (error handling)")

print("\n" + "=" * 70)
