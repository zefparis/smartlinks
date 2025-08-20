@echo off
echo Testing Python environment...
.venv\Scripts\python.exe test_env.py > test_output.txt 2>&1
type test_output.txt
pause
