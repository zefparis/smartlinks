@echo off
setlocal
pushd "%~dp0"

:: Backend (corrected uvicorn command)
start "Backend" cmd /k "call .venv\Scripts\activate && python -m uvicorn src.soft.router:app --host 127.0.0.1 --port 8000 --reload"

:: App Autopilot
start "Autopilot" cmd /k "call .venv\Scripts\activate && python -m src.soft.autopilot"

:: Frontend
start "Frontend" cmd /k "cd src\frontend && npm run dev"

echo ============================================
echo ✅ Tous les services sont lancés !
echo --------------------------------------------
echo Backend:   http://localhost:8000
echo Frontend:  http://localhost:5173
echo Admin:     http://localhost:8000/admin
echo IA Supervisor: http://localhost:8000/api/ia/status
echo ============================================

pause
popd
