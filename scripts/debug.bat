@echo off
REM Script Windows pour debug du système SmartLinks
REM Vérifie l'état des services et données

setlocal enabledelayedexpansion
cd /d "%~dp0\.."

echo ========================================
echo SMARTLINKS DEBUG - WINDOWS
echo ========================================

REM Vérifier l'environnement virtuel
if not exist ".venv\Scripts\python.exe" (
    echo ❌ Environnement virtuel non trouvé
    pause
    exit /b 1
)

echo 🔍 Vérification de l'état du système...
echo.

REM Vérifier les données
echo 📊 État de la base de données:
.venv\Scripts\python.exe scripts\generate_massive_data.py --verify-only

echo.
echo 🌐 Test des endpoints analytics:
echo.

REM Tester les endpoints (si le serveur tourne)
echo Tentative de connexion aux endpoints...
curl -s http://localhost:8000/api/analytics/health 2>nul
if %ERRORLEVEL% equ 0 (
    echo ✅ Backend accessible
    echo.
    echo 📈 Test endpoints analytics:
    echo    /api/analytics/health
    curl -s http://localhost:8000/api/analytics/health | python -m json.tool 2>nul
    echo.
    echo    /api/analytics/devices
    curl -s "http://localhost:8000/api/analytics/devices" 2>nul | python -c "import sys,json; data=json.load(sys.stdin); print(f'Devices: {len(data.get(\"devices\", []))} found')" 2>nul
    echo.
    echo    /api/analytics/countries  
    curl -s "http://localhost:8000/api/analytics/countries?days=7" 2>nul | python -c "import sys,json; data=json.load(sys.stdin); print(f'Countries: {len(data.get(\"countries\", []))} found')" 2>nul
    echo.
    echo    /api/analytics/traffic-by-segment
    curl -s "http://localhost:8000/api/analytics/traffic-by-segment?days=7" 2>nul | python -c "import sys,json; data=json.load(sys.stdin); print(f'Segments: {len(data.get(\"segments\", []))} found')" 2>nul
) else (
    echo ❌ Backend non accessible sur http://localhost:8000
    echo    Démarrez le backend avec: python main.py
)

echo.
echo 🔧 Vérification des fichiers critiques:
if exist "main.py" (echo ✅ main.py) else (echo ❌ main.py manquant)
if exist "src\soft\router.py" (echo ✅ router.py) else (echo ❌ router.py manquant)
if exist "src\soft\api\analytics_router.py" (echo ✅ analytics_router.py) else (echo ❌ analytics_router.py manquant)
if exist ".env" (echo ✅ .env) else (echo ❌ .env manquant)
if exist "smartlinks.db" (echo ✅ smartlinks.db) else (echo ❌ smartlinks.db manquant)

echo.
echo 📝 Logs récents:
if exist "autopilot.log" (
    echo Dernières lignes de autopilot.log:
    powershell "Get-Content autopilot.log -Tail 5" 2>nul
)

echo.
echo ========================================
echo RÉSUMÉ DEBUG
echo ========================================
echo.
echo 🔧 Actions possibles:
echo    scripts\seed.bat --clean     # Regénérer les données
echo    scripts\reset.bat            # Reset complet
echo    start_all.bat               # Démarrer tous les services
echo    python main.py              # Démarrer seulement le backend
echo.
pause
