@echo off
setlocal EnableDelayedExpansion

:: ===============================
:: 🚀 SmartLinks Quick Launcher
:: ===============================

echo [*] Démarrage des services SmartLinks...
echo.

:: Check if .env exists
if not exist .env (
    echo [!] Fichier .env introuvable. Utilisation de .env.example...
    copy .env.example .env >nul
)

:: Backend Server
start "Backend" /MIN cmd /k "echo [*] Démarrage du Backend... && call .venv\Scripts\activate && python -m src.soft.router || echo [!] Erreur lors du démarrage du Backend"

:: Wait for backend to start
timeout /t 3 /nobreak >nul

:: Autopilot
start "Autopilot" /MIN cmd /k "echo [*] Démarrage de l'Autopilot... && call .venv\Scripts\activate && python -m src.soft.autopilot || echo [!] Erreur lors du démarrage de l'Autopilot"

:: Frontend
start "Frontend" /MIN cmd /k "echo [*] Démarrage du Frontend... && cd src/frontend && npm run dev || echo [!] Erreur lors du démarrage du Frontend"

echo ============================================
echo ✅ Tous les services sont en cours de démarrage...
echo --------------------------------------------
echo Backend:   http://localhost:8000
echo Frontend:  http://localhost:5173
echo Admin:     http://localhost:8000/admin
echo ============================================
echo.
echo [*] Appuyez sur une touche pour arrêter tous les services...
pause >nul

echo.
echo [*] Arrêt des services...
taskkill /FI "WINDOWTITLE eq Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Autopilot*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend*" /T /F >nul 2>&1
echo [*] Services arrêtés.
