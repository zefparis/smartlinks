@echo off
set PYTHONPATH=%CD%\src
.venv\Scripts\uvicorn src.soft.router:app --reload --host 0.0.0.0 --port 8000 --log-level debug
