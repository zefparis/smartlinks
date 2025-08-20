"""Test détaillé pour vérifier le bon fonctionnement de pytest."""
import sys
import os
from pathlib import Path

def test_python_version():
    """Vérifie que la version de Python est 3.11 ou supérieure."""
    assert sys.version_info >= (3, 11), "Python 3.11 ou supérieur est requis"

def test_imports():
    """Teste l'importation des modules principaux."""
    try:
        import pytest
        import pandas
        import numpy
        from jinja2 import Environment
        print("Tous les imports ont réussi")
        assert True
    except ImportError as e:
        assert False, f"Échec d'importation: {e}"

def test_paths():
    """Vérifie que les chemins des fichiers de test sont corrects."""
    test_dir = Path(__file__).parent
    src_dir = test_dir.parent / "src"
    
    assert test_dir.exists(), "Le répertoire de test n'existe pas"
    assert src_dir.exists(), "Le répertoire src n'existe pas"
    
    # Vérifie la présence de fichiers importants
    assert (src_dir / "soft" / "dg" / "algorithms" / "reporting" / "report_generator.py").exists(), \
           "Le fichier report_generator.py est introuvable"
    assert (src_dir / "soft" / "dg" / "algorithms" / "reporting" / "report_sections.py").exists(), \
           "Le fichier report_sections.py est introuvable"

def test_environment():
    """Vérifie les variables d'environnement essentielles."""
    assert "PYTHONPATH" in os.environ, "PYTHONPATH n'est pas défini"
    assert str(Path(__file__).parent.parent) in os.environ["PYTHONPATH"], \
           "Le répertoire racine doit être dans PYTHONPATH"

if __name__ == "__main__":
    # Exécute les tests directement sans pytest
    for name, func in list(globals().items()):
        if name.startswith("test_") and callable(func):
            print(f"Exécution de {name}...")
            try:
                func()
                print(f"✅ {name} a réussi")
            except AssertionError as e:
                print(f"❌ {name} a échoué: {e}")
