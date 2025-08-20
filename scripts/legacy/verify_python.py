import sys

def main():
    print("=== Vérification de l'environnement Python ===\n")
    
    # Afficher les informations de base
    print(f"Python version: {sys.version}")
    print(f"Exécutable: {sys.executable}")
    print(f"\nRépertoire de travail: {os.getcwd()}")
    
    # Tester l'écriture de fichier
    try:
        with open("test_write.txt", "w") as f:
            f.write("Test d'écriture réussi!")
        print("\n✅ Test d'écriture réussi")
        os.remove("test_write.txt")
    except Exception as e:
        print(f"\n❌ Échec de l'écriture: {e}")
    
    # Tester l'importation de modules
    print("\n=== Test d'importation des modules ===\n")
    
    modules = ["os", "sys", "fastapi", "uvicorn", "sqlalchemy", "pydantic"]
    
    for module in modules:
        try:
            __import__(module)
            version = getattr(sys.modules[module], "__version__", "(version inconnue)")
            print(f"✅ {module} importé avec succès {version}")
        except ImportError:
            print(f"❌ Impossible d'importer {module}")
    
    print("\n=== Test terminé ===")

if __name__ == "__main__":
    import os
    main()
