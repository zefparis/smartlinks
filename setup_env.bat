@echo off
echo Setting up Python environment...

:: Check Python version
python --version
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH
    exit /b 1
)

:: Create and activate virtual environment
echo Creating virtual environment...
python -m venv .venv
if %ERRORLEVEL% NEQ 0 (
    echo Failed to create virtual environment
    exit /b 1
)

:: Activate the virtual environment
call .venv\Scripts\activate
if %ERRORLEVEL% NEQ 0 (
    echo Failed to activate virtual environment
    exit /b 1
)

:: Install required packages
echo Installing required packages...
pip install --upgrade pip
pip install fastapi uvicorn[standard] python-dotenv httpx
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install required packages
    exit /b 1
)

echo Environment setup complete!
echo To activate the virtual environment, run: .\.venv\Scripts\activate
