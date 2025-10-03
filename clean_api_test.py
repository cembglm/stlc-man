"""
Clean API test for environment setups
"""

import requests
import json
import time

def test_api_clean():
    """Clean API test with minimal output"""
    try:
        print("Testing API endpoint...")
        
        # Wait a moment for backend to start
        time.sleep(2)
        
        response = requests.get("http://localhost:8000/api/processes/test-code-generation/environment-setups")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                setups = data.get('data', [])
                print(f"✅ API Success: Found {len(setups)} environment setups")
                
                # Show first 3 with environment names
                print("\nFirst 3 environment setups:")
                for i, setup in enumerate(setups[:3], 1):
                    env_name = setup.get('environment_name', 'N/A')
                    language = setup.get('environment_info', {}).get('language', 'Unknown')
                    print(f"  {i}. {env_name} ({language})")
                
            else:
                print("❌ API returned success=False")
        else:
            print(f"❌ API Error: Status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend not running")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_api_clean()