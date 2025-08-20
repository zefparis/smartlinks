@echo off
setlocal

:: Set Python executable path
set PYTHON=c:\smartlinks-autopilot\.venv\Scripts\python.exe
set LOG_FILE=server_output.log

echo Starting server with logging to %LOG_FILE%
%PYTHON% -c "import sys; print('Python version:', sys.version)" > %LOG_FILE% 2>&1
%PYTHON% -c "import fastapi; print('FastAPI version:', fastapi.__version__)" >> %LOG_FILE% 2>&1
%PYTHON% -c "import uvicorn; print('Uvicorn version:', uvicorn.__version__)" >> %LOG_FILE% 2>&1

echo.
echo Starting FastAPI server...
%PYTHON% -c "import uvicorn; uvicorn.run('minimal_test:app', host='0.0.0.0', port=8000, log_level='debug')" >> %LOG_FILE% 2>&1

echo Server stopped. Check %LOG_FILE% for details.
