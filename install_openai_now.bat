@echo off
echo Installation OpenAI en cours...
cd /d "c:\smartlinks-autopilot"

echo Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat

echo Installation du module openai...
python -m pip install openai>=1.40.0

echo Verification...
python -c "import openai; print('OpenAI version:', openai.__version__)"

echo Test du serveur...
python -c "from src.soft.dg.ai.openai_factory import OPENAI_AVAILABLE; print('OpenAI disponible:', OPENAI_AVAILABLE)"

echo.
echo Installation terminee! Vous pouvez maintenant demarrer le serveur.
echo Tapez: python main.py
pause
