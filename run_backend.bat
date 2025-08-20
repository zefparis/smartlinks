@echo off
echo Starting SmartLinks Backend Server...
echo.

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

echo.
echo Starting backend server on port 8000...
echo Press Ctrl+C to stop the server
echo.

python start_backend_working.py

pause
