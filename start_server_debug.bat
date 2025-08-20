@echo off
setlocal

:: Set Python path to the virtual environment
set PYTHON_PATH=c:\smartlinks-autopilot\.venv\Scripts\python.exe

:: Set the main application file
set APP_FILE=simple_test.py

:: Set the module and app name
set MODULE_NAME=simple_test:app

:: Set host and port
set HOST=0.0.0.0
set PORT=8000

echo Starting FastAPI server with debug logging...
echo Python: %PYTHON_PATH%
echo Module: %MODULE_NAME%
echo Host: %HOST%
echo Port: %PORT%
echo.

:: Start the server with detailed logging
%PYTHON_PATH% -c "^
import logging; ^
logging.basicConfig( ^
    level=logging.DEBUG, ^
    format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s', ^
    handlers=[ ^
        logging.StreamHandler(), ^
        logging.FileHandler('server_debug.log') ^
    ] ^
); ^
logger = logging.getLogger('uvicorn'); ^
logger.setLevel(logging.DEBUG); ^
import uvicorn; ^
config = uvicorn.Config( ^
    'simple_test:app', ^
    host='0.0.0.0', ^
    port=8000, ^
    log_level='debug', ^
    reload=True, ^
    log_config=None ^
); ^
server = uvicorn.Server(config); ^
logger.info('Starting server...'); ^
server.run()"
