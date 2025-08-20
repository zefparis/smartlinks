@echo off
echo Starting FastAPI server...
python -u simple_test.py > server_output.txt 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error starting server. Check server_output.txt for details.
    type server_output.txt
) else (
    echo Server started successfully.
)
