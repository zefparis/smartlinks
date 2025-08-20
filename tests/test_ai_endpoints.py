#!/usr/bin/env python3
import requests
import sys
import os
sys.path.insert(0, '.')
sys.path.insert(0, 'src')

def test_ai_endpoints():
    print('🔍 Testing AI endpoints...')
    
    # Test backend health
    try:
        response = requests.get('http://localhost:8000/api/analytics/health', timeout=3)
        if response.status_code == 200:
            print('✅ Backend running')
        else:
            print('❌ Backend not responding')
            return
    except:
        print('❌ Backend not running')
        return

    # Test AI endpoints that might be failing
    ai_endpoints = [
        '/api/ai/dg',
        '/api/assistant/ask',
        '/api/dg/ask',
        '/api/ia/supervisor/status',
        '/api/routes'  # List all available routes
    ]

    for endpoint in ai_endpoints:
        try:
            if endpoint == '/api/assistant/ask':
                # POST endpoint needs data
                response = requests.post(f'http://localhost:8000{endpoint}', 
                                       json={"message": "test"}, timeout=3)
            else:
                response = requests.get(f'http://localhost:8000{endpoint}', timeout=3)
            print(f'{endpoint}: {response.status_code}')
            if response.status_code == 404:
                print(f'  ❌ Not found - router not registered')
            elif response.status_code >= 400:
                print(f'  ❌ Error: {response.text[:100]}')
        except Exception as e:
            print(f'{endpoint}: ERROR - {e}')

if __name__ == '__main__':
    test_ai_endpoints()
