@echo off
setlocal enabledelayedexpansion

:: Set paths
set PYTHON=c:\smartlinks-autopilot\.venv\Scripts\python.exe
set LOG_FILE=fastapi_debug.log

:: Clear previous log
echo Starting FastAPI server at %TIME% > %LOG_FILE%

echo [*] Starting FastAPI server with debug logging...
echo [*] Logging to %CD%\%LOG_FILE%
echo [*] Python: %PYTHON%

echo [*] Testing Python executable...
%PYTHON% --version >> %LOG_FILE% 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python executable not found at %PYTHON%
    exit /b %ERRORLEVEL%
)

echo [*] Testing FastAPI installation...
%PYTHON% -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')" >> %LOG_FILE% 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to import FastAPI. Check if it's installed in the virtual environment.
    exit /b %ERRORLEVEL%
)

echo [*] Starting FastAPI server...
%PYTHON% -c "import uvicorn; uvicorn.run('minimal_test:app', host='0.0.0.0', port=8000, log_level='debug')" >> %LOG_FILE% 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to start FastAPI server. Check %CD%\%LOG_FILE% for details.
) else (
    echo [*] FastAPI server started successfully.
)

pause
