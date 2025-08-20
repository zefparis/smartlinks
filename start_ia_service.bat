@echo off
echo Starting SmartLinks IA Service...
echo.

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Start the backend server
echo Starting backend server on port 8000...
python -m uvicorn src.soft.router:app --host 127.0.0.1 --port 8000 --reload --log-level info

pause
