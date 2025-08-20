@echo off
REM Script Windows pour génération de données SmartLinks
REM Optimisé pour éviter les problèmes de longueur de ligne de commande

setlocal enabledelayedexpansion
cd /d "%~dp0\.."

echo ========================================
echo SMARTLINKS DATA SEEDING - WINDOWS
echo ========================================

REM Vérifier que l'environnement virtuel existe
if not exist ".venv\Scripts\python.exe" (
    echo ❌ Environnement virtuel non trouvé
    echo Exécutez d'abord: python -m venv .venv
    echo Puis: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Paramètres par défaut
set DAYS=30
set VOLUME=high
set CLEAN=false

REM Parser les arguments
:parse_args
if "%1"=="" goto :run_seed
if "%1"=="--days" (
    set DAYS=%2
    shift
    shift
    goto :parse_args
)
if "%1"=="--volume" (
    set VOLUME=%2
    shift
    shift
    goto :parse_args
)
if "%1"=="--clean" (
    set CLEAN=true
    shift
    goto :parse_args
)
shift
goto :parse_args

:run_seed
echo 🚀 Génération de données...
echo    Jours: %DAYS%
echo    Volume: %VOLUME%
echo    Nettoyage: %CLEAN%
echo.

REM Construire la commande
set CMD=.venv\Scripts\python.exe scripts\generate_massive_data.py --days %DAYS% --volume %VOLUME%
if "%CLEAN%"=="true" (
    set CMD=!CMD! --clean
)

REM Exécuter la génération
echo Commande: %CMD%
echo.
%CMD%

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ Erreur lors de la génération
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ✅ Génération terminée avec succès!
echo.
echo 🔄 Pour démarrer le système complet:
echo    start_all.bat
echo.
pause
