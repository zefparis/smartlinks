@echo off
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8

echo Starting server with logging...
python -u start_backend.py > server.log 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo Error starting server. Check server.log for details.
    type server.log
) else (
    echo Server started successfully. Check server.log for output.
)
