@echo off
echo Installation du module OpenAI...
cd /d "c:\smartlinks-autopilot"
.venv\Scripts\python.exe -m pip install openai>=1.40.0
echo.
echo Verification de l'installation...
.venv\Scripts\python.exe -c "import openai; print('OpenAI version:', openai.__version__)"
echo.
echo Installation terminee. Vous pouvez maintenant demarrer le serveur.
pause
