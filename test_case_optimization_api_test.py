#!/usr/bin/env python3
"""
Test script for Test Case Optimization API integration with Gemini
"""
import requests
import json
import sys

def test_test_case_optimization_api():
    """Test Test Case Optimization API with Gemini models"""
    
    print("🧪 Testing Test Case Optimization API integration...")
    
    # Test endpoints
    endpoints = {
        "models": "http://localhost:8000/api/test-case-optimization/models",
        "process_titles": "http://localhost:8000/api/test-case-optimization/process-titles-with-counts",
        "smart_selection": "http://localhost:8000/api/test-case-optimization/smart-selection"
    }
    
    print(f"📡 Testing endpoints:")
    for name, url in endpoints.items():
        print(f"   - {name}: {url}")
    
    # Test 1: Models endpoint
    print("\n🔍 Test 1: Getting available models...")
    try:
        response = requests.get(endpoints["models"], timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])
            gemini_models = [m for m in models if "gemini" in m.get("key", "").lower()]
            
            print(f"   ✅ Found {len(models)} total models")
            print(f"   🎯 Gemini models: {len(gemini_models)}")
            for model in gemini_models:
                print(f"      - {model.get('key')}: {model.get('name')} ({model.get('type', 'unknown')})")
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Process titles endpoint
    print("\n🔍 Test 2: Getting process titles...")
    try:
        response = requests.get(endpoints["process_titles"], timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            process_data = data.get("data", [])
            print(f"   ✅ Found {len(process_data)} processes")
            for proc in process_data[:3]:  # Show first 3
                print(f"      - {proc.get('process_title')}: {proc.get('test_case_count')} test cases")
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 3: Smart selection endpoint (with placeholder API key)
    print("\n🔍 Test 3: Testing smart selection endpoint...")
    
    # Sample test data
    test_data = {
        "selected_test_cases": [
            {
                "ScenarioID": "TS_001",
                "TestCaseID": "TC_001",
                "Title": "User Login Test",
                "Description": "Test user login functionality",
                "Objective": "Verify user can login successfully",
                "Category": "Positive",
                "SelectedTestType": "Functional",
                "SelectedCategory": "Authentication"
            },
            {
                "ScenarioID": "TS_001", 
                "TestCaseID": "TC_002",
                "Title": "User Login Validation",
                "Description": "Test user login with validation",
                "Objective": "Verify login validation works",
                "Category": "Positive",
                "SelectedTestType": "Functional",
                "SelectedCategory": "Authentication"
            }
        ],
        "process_titles": ["Test Process 1"],
        "process_name": "API Integration Test",
        "selected_model": "gemini-2.5-flash",
        "optimization_type": "individual",
        "api_key": "AIzaSyCYour_Real_API_Key_Here"  # Placeholder key
    }
    
    try:
        response = requests.post(endpoints["smart_selection"], json=test_data, timeout=60)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Success! Response received:")
            print(f"      - Success: {data.get('success')}")
            print(f"      - Message: {data.get('message', 'No message')}")
            
            if 'data' in data:
                result_data = data['data']
                print(f"      - Original count: {result_data.get('original_count', 'N/A')}")
                print(f"      - Unique count: {result_data.get('unique_count', 'N/A')}")
                print(f"      - Optimization rate: {result_data.get('optimization_rate', 'N/A')}")
                
        elif response.status_code == 400:
            print("   ⚠️  Bad Request (expected with placeholder API key)")
            try:
                error_data = response.json()
                print(f"      Error: {error_data.get('detail', 'No details')}")
            except:
                print(f"      Raw response: {response.text}")
                
        elif response.status_code == 500:
            print("   ❌ Internal Server Error")
            try:
                error_data = response.json()
                print(f"      Error: {error_data.get('detail', 'No details')}")
            except:
                print(f"      Raw response: {response.text}")
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
            print(f"      Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print("\n📋 Summary:")
    print("   - Models endpoint: Should return Gemini models")
    print("   - Process titles endpoint: Should return available processes") 
    print("   - Smart selection endpoint: Should handle API key validation")
    print("\n💡 To test with real API key:")
    print("   1. Replace 'AIzaSyCYour_Real_API_Key_Here' with actual Google API key")
    print("   2. Ensure you have test cases in the database")
    print("   3. Run the test again")

if __name__ == "__main__":
    print("="*70)
    print("🚀 TEST CASE OPTIMIZATION API INTEGRATION TEST")
    print("="*70)
    test_test_case_optimization_api()