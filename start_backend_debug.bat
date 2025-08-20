@echo off
echo Starting SmartLinks Backend with IA Service Debug...
echo.

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Check Python and dependencies
echo Checking Python environment...
python --version
python -c "import sys; print('Python path:', sys.executable)"

REM Load environment and test IA service
echo.
echo Testing IA Service initialization...
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'MISSING')"

REM Test IA Supervisor import and initialization
echo.
echo Testing IA Supervisor...
python -c "import sys; sys.path.append('.'); from src.soft.dg.ai.supervisor import IASupervisor; print('IASupervisor import: OK')"

REM Start the server
echo.
echo Starting FastAPI server...
python -m uvicorn src.soft.router:app --host 127.0.0.1 --port 8000 --reload --log-level info

pause
