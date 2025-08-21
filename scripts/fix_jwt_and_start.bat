@echo off
REM Diagnostic + auto-fix PyJWT, alignement venv + start Uvicorn

REM Set path vars
set VENV_PATH=%CD%\.venv\Scripts
set PYTHON=%VENV_PATH%\python.exe
set PIP=%VENV_PATH%\pip.exe

echo === CHECK PyJWT ===
%PYTHON% -c "import jwt; print(jwt.__version__)" 2>NUL
IF %ERRORLEVEL% NEQ 0 (
    echo PyJWT absent, correction...
    %PIP% uninstall -y jwt
    %PIP% install PyJWT==2.8.0
)

REM Check si PyJWT est dans requirements.txt
findstr /C:"PyJWT" requirements.txt >NUL
IF %ERRORLEVEL% NEQ 0 (
    echo PyJWT==2.8.0 >> requirements.txt
)

echo === PIP INSTALL -R ===
%PIP% install -r requirements.txt

echo === WHERE UVICORN ===
where uvicorn

echo === START UVICORN ===
%PYTHON% -m uvicorn src.backend.main:app --reload
