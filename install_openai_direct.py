import subprocess
import sys
import os

# Installation directe du module openai
venv_python = r"c:\smartlinks-autopilot\.venv\Scripts\python.exe"

print("Installation openai...")
os.system(f'"{venv_python}" -m pip install openai>=1.40.0')

print("Vérification...")
os.system(f'"{venv_python}" -c "import openai; print(f\'OpenAI installé: {{openai.__version__}}\')"')

print("Test import...")
sys.path.insert(0, r"c:\smartlinks-autopilot\.venv\Lib\site-packages")
try:
    import openai
    print(f"✅ OpenAI disponible: {openai.__version__}")
except ImportError as e:
    print(f"❌ Erreur import: {e}")
