import requests
import os
from dotenv import load_dotenv

load_dotenv()

SEOMONITOR_API_KEY = os.getenv("SEOMONITOR_API_KEY")
BASE_URL = "https://apigw.seomonitor.com/v3"

def test_api_endpoint(endpoint_name="campaigns", mock=False):
    """
    Test SEOmonitor API endpoints
    Available endpoints:
    - campaigns: Get tracked campaigns
    - keywords: Get keywords data
    - competitors: Get competitors data
    - visibility: Get visibility data
    - forecasts: Get forecasts data
    - Add more as needed
    """
    
    if mock or not SEOMONITOR_API_KEY:
        return {
            "success": True,
            "endpoint": endpoint_name,
            "data": {
                "campaign_info": {
                    "id": "74516",
                    "name": "Demo Campaign",
                    "domain": "www.example.com",
                    "keyword_count": 588
                },
                "visibility": {
                    "desktop": {"latest": 0.28},
                    "mobile": {"latest": 0.27}
                }
            },
            "message": "🧪 Mock data (Set SEOMONITOR_API_KEY for real data)"
        }
    
    # Map endpoint names to API paths
    endpoints = {
        "campaigns": "/dashboard/v3.0/campaigns/tracked",
        "keywords": "/rank-tracker/v3.0/keywords",
        "competitors": "/rank-tracker/v3.0/competitors",
        "visibility": "/rank-tracker/v3.0/visibility",
        "forecasts": "/forecasting/v3.0/forecasts",
        # Add more endpoints as needed
    }
    
    if endpoint_name not in endpoints:
        return {
            "success": False,
            "error": f"Unknown endpoint: {endpoint_name}. Available: {', '.join(endpoints.keys())}"
        }
    
    url = BASE_URL + endpoints[endpoint_name]
    headers = {
        "Accept": "application/json",
        "Authorization": SEOMONITOR_API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {
                "success": True,
                "endpoint": endpoint_name,
                "data": response.json(),
                "message": f"✅ API call successful"
            }
        else:
            return {
                "success": False,
                "endpoint": endpoint_name,
                "status_code": response.status_code,
                "error": response.text,
                "message": f"❌ API returned {response.status_code}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "endpoint": endpoint_name,
            "error": str(e),
            "message": f"❌ Request failed: {str(e)}"
        }

if __name__ == "__main__":
    # Test with mock data
    result = test_api_endpoint("campaigns", mock=True)
    print(result)
