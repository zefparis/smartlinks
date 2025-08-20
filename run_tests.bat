@echo off
setlocal enabledelayedexpansion

echo ===== Test d'environnement =====
python -c "import sys; print('Python version:', sys.version)"
python -c "import os; print('Répertoire de travail:', os.getcwd())"

echo.
echo ===== Test d'importation =====
python -c "try: import pytest; print('pytest version:', pytest.__version__); except ImportError as e: print('Erreur:', e)"
python -c "try: import pandas; print('pandas version:', pandas.__version__); except ImportError as e: print('Erreur:', e)"
python -c "try: import numpy; print('numpy version:', numpy.__version__); except ImportError as e: print('Erreur:', e)"
python -c "try: from jinja2 import Environment; print('jinja2 est installé'); except ImportError as e: print('Erreur:', e)"

echo.
echo ===== Exécution des tests =====
python -m pytest tests/test_simple.py -v

pause
