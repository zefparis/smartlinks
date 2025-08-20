@echo off
echo Installing croniter dependency...
cd /d "c:\smartlinks-autopilot"
.venv\Scripts\pip.exe install croniter
echo Testing import...
.venv\Scripts\python.exe -c "import croniter; print('croniter installed successfully')"
echo Done.
