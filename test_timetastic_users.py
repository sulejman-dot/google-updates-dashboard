#!/usr/bin/env python3
"""
Test Timetastic API - Get Users Endpoint
The absences endpoint doesn't return emails, so we need to get user details separately
"""

import requests
import json

API_TOKEN = "05e639d8-4f09-4b5a-ad2b-1bf39d2bae4f"

print("=" * 70)
print("TESTING TIMETASTIC /api/users ENDPOINT")
print("=" * 70)

# Try to get all users to map userId to email
users_url = "https://app.timetastic.co.uk/api/users"
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(users_url, headers=headers)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        users = response.json()
        print(f"\nTotal Users: {len(users)}")
        print("\nUser Details (first 5):")
        for user in users[:5]:
            print(f"\n  User ID: {user.get('id')}")
            print(f"  Name: {user.get('firstname')} {user.get('surname')}")
            print(f"  Email: {user.get('email')}")
            print(f"  Department: {user.get('departmentName')}")
        
        # Now let's find the absent users
        print("\n" + "=" * 70)
        print("MATCHING ABSENT USERS WITH EMAILS")
        print("=" * 70)
        
        absent_user_ids = [208777, 778639, 515385]  # From the absences response
        absent_names = ["Cosmin Negrescu", "Claudiu Stanciu", "Delia Dragan"]
        
        print(f"\nAbsent User IDs: {absent_user_ids}")
        
        # Create a mapping of userId to email
        user_map = {user['id']: user for user in users}
        
        print("\nAbsent Users with Emails:")
        for user_id, name in zip(absent_user_ids, absent_names):
            if user_id in user_map:
                user = user_map[user_id]
                print(f"  - {name}")
                print(f"    Email: {user.get('email')}")
                print(f"    Department: {user.get('departmentName')}")
            else:
                print(f"  - {name} (User ID {user_id} not found)")
        
        print("\n✅ Solution: Use /api/users to get email mapping!")
        
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
