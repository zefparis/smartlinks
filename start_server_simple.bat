@echo off
set PYTHONPATH=%~dp0
.venv\Scripts\python.exe -m uvicorn src.soft.router:app --reload --host 0.0.0.0 --port 8000
