#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '.')
sys.path.insert(0, 'src')

print('🚀 Starting SmartLinks Backend')
print('Host: http://localhost:8000')
print('Analytics: http://localhost:3000/analytics')
print('-' * 40)

try:
    from main import app
    import uvicorn
    
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
    input('Press Enter to exit...')
