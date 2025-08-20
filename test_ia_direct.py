#!/usr/bin/env python3
"""
Direct test script for IA service endpoints
"""
import requests
import json
import sys

def test_ia_health():
    """Test IA health endpoint"""
    try:
        print("Testing IA health endpoint...")
        response = requests.get('http://localhost:8000/api/ia/health', timeout=10)
        print(f"Health Status: {response.status_code}")
        print(f"Health Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_ia_status():
    """Test IA status endpoint"""
    try:
        print("\nTesting IA status endpoint...")
        response = requests.get('http://localhost:8000/api/ia/status', timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Status Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Status check failed: {e}")
        return False

def test_ia_ask():
    """Test IA ask endpoint"""
    try:
        print("\nTesting IA ask endpoint...")
        payload = {"question": "Hello, are you working correctly?"}
        response = requests.post(
            'http://localhost:8000/api/ia/ask', 
            json=payload, 
            timeout=30
        )
        print(f"Ask Status: {response.status_code}")
        print(f"Ask Response: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Parsed Response: {json.dumps(data, indent=2)}")
            except:
                print("Could not parse JSON response")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Ask test failed: {e}")
        return False

def main():
    """Run all IA tests"""
    print("=== SmartLinks IA Service Direct Test ===\n")
    
    results = []
    results.append(("Health Check", test_ia_health()))
    results.append(("Status Check", test_ia_status()))
    results.append(("Ask Test", test_ia_ask()))
    
    print("\n=== Test Results ===")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
