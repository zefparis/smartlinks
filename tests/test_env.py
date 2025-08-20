"""Test minimal pour vérifier l'environnement d'exécution."""
import sys
import os

def main():
    print("=== Test d'environnement ===")
    print(f"Python version: {sys.version}")
    print(f"Répertoire de travail: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Non défini')}")
    print("\n=== Tests d'importation ===")
    
    # Test d'importation des dépendances
    try:
        import pytest
        print(f"✅ pytest version: {pytest.__version__}")
    except ImportError:
        print("❌ pytest n'est pas installé")
    
    try:
        import pandas
        print(f"✅ pandas version: {pandas.__version__}")
    except ImportError:
        print("❌ pandas n'est pas installé")
    
    try:
        import numpy
        print(f"✅ numpy version: {numpy.__version__}")
    except ImportError:
        print("❌ numpy n'est pas installé")
    
    try:
        from jinja2 import Environment
        print("✅ jinja2 est installé")
    except ImportError:
        print("❌ jinja2 n'est pas installé")
    
    print("\n=== Vérification des chemins ===")
    
    # Vérification des chemins
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_dir = os.path.join(base_dir, "src")
    
    print(f"Répertoire de base: {base_dir}")
    print(f"Répertoire src: {src_dir}")
    
    # Vérification des fichiers importants
    important_files = [
        ("report_generator.py", os.path.join(src_dir, "soft", "dg", "algorithms", "reporting", "report_generator.py")),
        ("report_sections.py", os.path.join(src_dir, "soft", "dg", "algorithms", "reporting", "report_sections.py")),
    ]
    
    for name, path in important_files:
        if os.path.exists(path):
            print(f"✅ {name} trouvé: {path}")
        else:
            print(f"❌ {name} introuvable: {path}")
    
    print("\n=== Fin du test d'environnement ===")

if __name__ == "__main__":
    main()
