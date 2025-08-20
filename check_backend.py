#!/usr/bin/env python3
import requests
import sys
import os

def check_backend():
    print('🔍 Checking backend status...')
    try:
        response = requests.get('http://localhost:8000/api/analytics/health', timeout=3)
        print(f'✅ Backend status: {response.status_code}')
        if response.status_code == 200:
            print('Backend is running - testing analytics endpoints...')
            endpoints = [
                '/api/analytics/devices',
                '/api/analytics/countries', 
                '/api/analytics/clicks/history'
            ]
            for endpoint in endpoints:
                resp = requests.get(f'http://localhost:8000{endpoint}', timeout=2)
                print(f'{endpoint}: {resp.status_code}')
            print('Analytics page should work now!')
        return True
    except requests.exceptions.ConnectionError:
        print('❌ Backend not running')
        return False
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

def start_backend():
    sys.path.insert(0, '.')
    sys.path.insert(0, 'src')
    
    print('🚀 Starting backend server...')
    from main import app
    import uvicorn
    
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')

if __name__ == '__main__':
    if not check_backend():
        start_backend()
