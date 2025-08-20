@echo off
cd /d "C:\smartlinks-autopilot"
echo Starting SmartLinks Backend Server...
echo Working directory: %CD%
echo.
python -m uvicorn src.soft.router:app --host 127.0.0.1 --port 8000 --reload
echo.
echo Server stopped. Press any key to exit...
pause
echo Analytics: http://localhost:3000/analytics
echo ========================================
echo.

cd /d "%~dp0"

python -c "
import sys
import os
sys.path.insert(0, '.')
sys.path.insert(0, 'src')

print('✅ Loading application...')
from main import app
import uvicorn

print('🌐 Starting server on port 8000...')
uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')
"

echo.
echo Server stopped.
pause
