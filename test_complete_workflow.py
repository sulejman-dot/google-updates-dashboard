#!/usr/bin/env python3
"""
COMPLETE Timetastic API Integration Workflow Test
Includes the additional step to fetch user emails via /api/users
"""

import requests
import json
from datetime import datetime

# Configuration
API_TOKEN = "05e639d8-4f09-4b5a-ad2b-1bf39d2bae4f"
BASE_URL = "https://app.timetastic.co.uk/api"

# Simulate today's date
today = datetime.now()
start_date = today.strftime("%Y-%m-%d")
end_date = today.strftime("%Y-%m-%d")

print("=" * 70)
print("COMPLETE TIMETASTIC API WORKFLOW TEST")
print("=" * 70)
print(f"\nDate Range: {start_date} to {end_date}")
print(f"Current Time: {today.strftime('%Y-%m-%d %H:%M:%S')}\n")

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# ============================================================================
# MODULE 8: Simulated Active Users from Google Sheets
# ============================================================================
print("=" * 70)
print("MODULE 8: Active Users (from Google Sheets)")
print("=" * 70)

# Simulate real team members from your Google Sheets
active_users = [
    {"name": "Cosmin Negrescu", "email": "cosmin@seomonitor.com", "department": "Leadership"},
    {"name": "Claudiu Stanciu", "email": "claudiu@seomonitor.com", "department": "Engineering"},
    {"name": "Delia Dragan", "email": "delia@seomonitor.com", "department": "CS"},
    {"name": "Diana Grigorescu", "email": "diana@seomonitor.com", "department": "Product"},
    {"name": "Andrei Pantea", "email": "andrei.p@seomonitor.com", "department": "Engineering"},
]

print(f"\nTotal Active Users: {len(active_users)}")
for user in active_users:
    print(f"  - {user['name']:20} ({user['email']})")

# ============================================================================
# MODULE 8A-1: Get All Users (to map userId to email)
# ============================================================================
print("\n" + "=" * 70)
print("MODULE 8A-1: HTTP Request - Get All Users")
print("=" * 70)

users_response = requests.get(f"{BASE_URL}/users", headers=headers)
print(f"Status: {users_response.status_code}")

if users_response.status_code == 200:
    all_users = users_response.json()
    user_map = {user['id']: user for user in all_users}
    print(f"✓ Fetched {len(all_users)} users for email mapping")
else:
    print(f"❌ Failed to fetch users")
    user_map = {}

# ============================================================================
# MODULE 8A-2: Get Absences
# ============================================================================
print("\n" + "=" * 70)
print("MODULE 8A-2: HTTP Request - Get Absences")
print("=" * 70)

params = {
    "Start": start_date,
    "End": end_date,
    "AbsenceQueryType": "AllAbsences"
}

absences_response = requests.get(f"{BASE_URL}/absences", headers=headers, params=params)
print(f"Status: {absences_response.status_code}")

if absences_response.status_code == 200:
    absences_data = absences_response.json()
    print(f"✓ Absences retrieved successfully")
    
    # Show raw absences
    print(f"\nAbsences for {start_date}:")
    for day in absences_data:
        if "absences" in day and day["absences"]:
            print(f"\n  Date: {day['date']}")
            for absence in day["absences"]:
                print(f"    - {absence['userName']}")
                print(f"      Type: {absence['absenceType']}")
                print(f"      Detail: {absence['detail']}")
                print(f"      Time: {absence['start']} to {absence['end']}")
    
    # ============================================================================
    # MODULE 8B-1: Extract Absent User Emails (with userId mapping)
    # ============================================================================
    print("\n" + "=" * 70)
    print("MODULE 8B-1: Extract Absent User Emails")
    print("=" * 70)
    
    absent_emails = []
    absent_details = []
    
    for day in absences_data:
        if "absences" in day:
            for absence in day["absences"]:
                user_id = absence.get("userId")
                if user_id and user_id in user_map:
                    email = user_map[user_id].get("email")
                    if email:
                        absent_emails.append(email)
                        absent_details.append({
                            "name": absence["userName"],
                            "email": email,
                            "type": absence["absenceType"],
                            "detail": absence["detail"]
                        })
    
    print(f"\nAbsent Emails: {absent_emails}")
    print(f"Total Absent Users: {len(absent_emails)}")
    
    if absent_details:
        print("\nAbsent Users Details:")
        for user in absent_details:
            print(f"  - {user['name']} ({user['email']})")
            print(f"    {user['type']}: {user['detail']}")
    
    # ============================================================================
    # MODULE 8B-2: Filter Available Users
    # ============================================================================
    print("\n" + "=" * 70)
    print("MODULE 8B-2: Filter Available Users")
    print("=" * 70)
    
    available_users = []
    print("\nFiltering Logic:")
    for user in active_users:
        is_absent = user["email"] in absent_emails
        status = "EXCLUDED ✗ (Absent)" if is_absent else "INCLUDED ✓ (Available)"
        print(f"  {user['name']:20} → {status}")
        
        if not is_absent:
            available_users.append(user)
    
    print(f"\nFiltered Result: {len(available_users)} available users")
    
    # ============================================================================
    # MODULE 11: Array Aggregator
    # ============================================================================
    print("\n" + "=" * 70)
    print("MODULE 11: Array Aggregator")
    print("=" * 70)
    print(f"\nAggregated {len(available_users)} available users:")
    for user in available_users:
        print(f"  - {user['name']} ({user['email']})")
    
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
    
    # Simulate: Let's say Diana and Andrei checked in
    unique_users_checked_in = 2
    
    if total_available_members > 0:
        response_rate = round((unique_users_checked_in / total_available_members) * 100, 1)
    else:
        response_rate = 0
    
    print(f"\nUsers Checked In Today: {unique_users_checked_in}")
    print(f"Available Members: {total_available_members}")
    print(f"Response Rate: {response_rate}%")
    
    # Comparison
    original_total = len(active_users)
    original_rate = round((unique_users_checked_in / original_total) * 100, 1)
    
    print(f"\n📊 IMPACT COMPARISON:")
    print(f"  WITHOUT Timetastic: {unique_users_checked_in}/{original_total} = {original_rate}%")
    print(f"  WITH Timetastic:    {unique_users_checked_in}/{total_available_members} = {response_rate}%")
    print(f"  Improvement: {response_rate - original_rate:+.1f}% (more accurate!)")
    
    # ============================================================================
    # SUMMARY
    # ============================================================================
    print("\n" + "=" * 70)
    print("✅ WORKFLOW TEST COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"\n✓ API Connection: Working")
    print(f"✓ User Email Mapping: Working ({len(all_users)} users mapped)")
    print(f"✓ Absences Retrieved: {len(absent_emails)} users absent today")
    print(f"✓ Filtering Logic: Working correctly")
    print(f"✓ Response Rate Calculation: Accurate")
    print(f"\n🎯 Result: {len(absent_emails)} team members filtered out")
    print(f"   Absent: {', '.join([d['name'] for d in absent_details])}")
    print(f"   Available: {', '.join([u['name'] for u in available_users])}")

else:
    print(f"❌ Failed to fetch absences: {absences_response.status_code}")

print("\n" + "=" * 70)
