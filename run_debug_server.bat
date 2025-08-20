@echo off
setlocal

:: Set Python path to the virtual environment
set PYTHON=c:\smartlinks-autopilot\.venv\Scripts\python.exe
set SCRIPT=verify_fastapi.py

:: Create a log file with timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "timestamp=%dt:~0,8%-%dt:~8,6%"
set LOG_FILE=server_%timestamp%.log

echo Starting FastAPI server with debug logging...
echo Python: %PYTHON%
echo Script: %SCRIPT%
echo Log file: %LOG_FILE%
echo.

:: Start the server with detailed logging
%PYTHON% -c "
import sys
import logging

# Configure logging to both console and file
logging.basicConfig(
    level=logging.DEBUG,
    format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('%LOG_FILE%')
    ]
)

logger = logging.getLogger('uvicorn')
logger.setLevel(logging.DEBUG)

# Log environment information
logger.info('Python: %s', sys.version)
logger.info('Executable: %s', sys.executable)
logger.info('Working directory: %s', os.getcwd())

# Import and run FastAPI
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get('/test')
async def test():
    logger.info('Test endpoint called')
    return {'status': 'ok'}

logger.info('Starting Uvicorn server...')
uvicorn.run(
    app,
    host='0.0.0.0',
    port=8000,
    log_level='debug',
    reload=True
)
"
