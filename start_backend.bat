@echo off
echo 🚀 Starting SmartLinks Backend Server
echo Host: http://localhost:8000
echo Analytics: http://localhost:3000/analytics
echo.
echo Press Ctrl+C to stop the server
echo ========================================

cd /d "%~dp0"
python -c "
import sys
import os
sys.path.insert(0, '.')
sys.path.insert(0, 'src')

try:
    from soft.router import app
    import uvicorn
    print('✅ Backend loaded successfully')
    uvicorn.run(app, host='127.0.0.1', port=8000, log_level='info')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    input('Press Enter to exit...')
"

pause
