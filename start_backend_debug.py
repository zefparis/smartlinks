#!/usr/bin/env python3
"""
Debug script to start SmartLinks backend with detailed error reporting
"""
import sys
import os
import traceback

# Add paths
sys.path.append('.')
sys.path.append('src')

def start_backend():
    print('🚀 STARTING SMARTLINKS BACKEND')
    print('=' * 50)
    
    try:
        print('Step 1: Environment setup...')
        print(f'   Python: {sys.version}')
        print(f'   Working dir: {os.getcwd()}')
        
        print('Step 2: Loading environment...')
        from dotenv import load_dotenv
        load_dotenv()
        print('   ✅ Environment loaded')
        
        print('Step 3: Importing main app...')
        from main import app
        print('   ✅ FastAPI app imported')
        
        print('Step 4: Testing database connection...')
        from soft.db import get_db
        db_gen = get_db()
        db = next(db_gen)
        print('   ✅ Database connection OK')
        
        print('Step 5: Testing endpoints with TestClient...')
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get('/api/analytics/health')
        print(f'   Health endpoint: {response.status_code}')
        
        if response.status_code != 200:
            print(f'   ❌ Health failed: {response.text}')
            return False
        
        # Test other endpoints
        test_endpoints = [
            '/api/analytics/devices',
            '/api/analytics/countries', 
            '/api/analytics/clicks/history',
            '/api/settings'
        ]
        
        for endpoint in test_endpoints:
            try:
                resp = client.get(endpoint)
                status = '✅' if resp.status_code == 200 else '⚠️'
                print(f'   {endpoint}: {status} {resp.status_code}')
            except Exception as e:
                print(f'   {endpoint}: ❌ {e}')
        
        print('\nStep 6: Starting live server on port 8000...')
        import uvicorn
        
        # Start server
        uvicorn.run(
            app, 
            host='127.0.0.1', 
            port=8000, 
            log_level='info',
            access_log=True
        )
        
    except ImportError as e:
        print(f'\n❌ IMPORT ERROR: {e}')
        print('\nFull traceback:')
        traceback.print_exc()
        return False
        
    except Exception as e:
        print(f'\n❌ STARTUP ERROR: {e}')
        print('\nFull traceback:')
        traceback.print_exc()
        return False

if __name__ == '__main__':
    start_backend()
