import os
import requests
from dotenv import load_dotenv

def test_token(token=None):
    if not token:
        load_dotenv()
        token = os.getenv("TIMETASTIC_API_TOKEN")
    
    if not token:
        print("❌ Error: No token provided and TIMETASTIC_API_TOKEN not found in .env")
        return False

    endpoints = [
        "https://app.timetastic.co.uk/api/users",
        "https://app.timetastic.co.uk/api/holidays",
        "https://app.timetastic.co.uk/api/leaves"
    ]
    
    headers = {
        "Authorization": f"Bearer {token}"
    }

    print(f"📡 Testing Timetastic API token with multiple endpoints...")
    
    for url in endpoints:
        try:
            print(f"\n🔍 Testing {url}...")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                print(f"✅ Success! {url} returned 200 OK.")
                try:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        print(f"📦 Data found: {len(data)} items.")
                    elif isinstance(data, dict):
                        print(f"👤 Data: {data.get('firstname', 'No Name')} {data.get('surname', '')}")
                except:
                    print("📦 Success, but could not parse JSON body.")
                return True
            elif response.status_code == 401:
                print(f"❌ 401 Unauthorized: Token is invalid.")
                return False
            elif response.status_code == 404:
                print(f"❓ 404 Not Found: Endpoint does not exist.")
            else:
                print(f"⚠️  Returned status code {response.status_code}")
                # print(response.text[:200]) # Print first 200 chars of body for debug
        except Exception as e:
            print(f"❌ Error during request to {url}: {str(e)}")
    
    return False

if __name__ == "__main__":
    # Test with provided token if available
    token = "05e639d8-4f09-4b5a-ad2b-1bf39d2bae4f"
    test_token(token)
