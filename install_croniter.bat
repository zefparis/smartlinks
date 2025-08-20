@echo off
echo Installing croniter dependency...
cd /d "c:\smartlinks-autopilot"
call .venv\Scripts\activate.bat
pip install croniter
echo Installation complete.
