@echo off
echo Installing missing dependencies...
cd /d "c:\smartlinks-autopilot"
.venv\Scripts\pip.exe install croniter>=1.3.0
echo croniter installation complete.
echo Testing import...
.venv\Scripts\python.exe -c "import croniter; print('croniter imported successfully')"
pause
