@echo off
set PYTHONUNBUFFERED=1
python -u -c "import logging; logging.basicConfig(level=logging.INFO); from src.soft.router import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')"
