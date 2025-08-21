@echo off
echo Checking SmartLinks Autopilot dependencies...
python scripts/check_dependencies.py
if %errorlevel% neq 0 (
    echo Dependency check failed. Please review the logs above.
    exit /b %errorlevel%
)
echo Dependency check completed successfully.
