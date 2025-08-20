@echo off
echo Installing croniter dependency for RCP system...
cd /d "c:\smartlinks-autopilot"
echo Current directory: %CD%
echo.
echo Installing croniter...
.venv\Scripts\pip.exe install croniter>=1.3.0
echo.
echo Testing import...
.venv\Scripts\python.exe -c "import croniter; print('SUCCESS: croniter is now available')"
echo.
echo croniter installation complete!
echo You can now restart the backend server.
pause
