import sys
from pathlib import Path

# Ajoute le répertoire src au PYTHONPATH
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

# Importe et exécute l'application
from main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
