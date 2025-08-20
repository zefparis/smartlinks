@echo off
REM Script Windows pour reset complet de la base SmartLinks
REM Nettoie et regénère toutes les données

setlocal enabledelayedexpansion
cd /d "%~dp0\.."

echo ========================================
echo SMARTLINKS RESET COMPLET - WINDOWS
echo ========================================

REM Vérifier l'environnement virtuel
if not exist ".venv\Scripts\python.exe" (
    echo ❌ Environnement virtuel non trouvé
    pause
    exit /b 1
)

echo ⚠️  ATTENTION: Cette opération va:
echo    - Supprimer toutes les données existantes
echo    - Regénérer des données de test complètes
echo    - Redémarrer les services
echo.
set /p CONFIRM="Continuer? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo Opération annulée
    exit /b 0
)

echo.
echo 🧹 Nettoyage et régénération...
.venv\Scripts\python.exe scripts\generate_massive_data.py --clean --days 30 --volume high

if %ERRORLEVEL% neq 0 (
    echo ❌ Erreur lors du reset
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ✅ Reset terminé!
echo.
echo 🚀 Démarrage des services...
call start_all.bat

echo.
echo ✅ Système prêt!
echo    Frontend: http://localhost:3000
echo    Backend API: http://localhost:8000
echo    Analytics: http://localhost:3000/analytics
pause
