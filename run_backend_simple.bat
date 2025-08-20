@echo off
echo Starting SmartLinks Backend Server...
cd /d "c:\smartlinks-autopilot"
call .venv\Scripts\activate.bat
cd src
python -m uvicorn soft.router:app --host 127.0.0.1 --port 8000 --reload
pause
