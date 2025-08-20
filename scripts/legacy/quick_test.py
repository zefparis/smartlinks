print("=== Test de base de Python ===")
print("Ce message devrait s'afficher si Python fonctionne correctement.")

# Tester l'importation de modules
try:
    import sys
    print(f"\nPython version: {sys.version}")
    print(f"Chemin d'exécution: {sys.executable}")
    print("\nChemin de recherche Python (sys.path):")
    for p in sys.path:
        print(f"  {p}")
    print("\nTest réussi!")
except Exception as e:
    print(f"\n❌ Erreur lors du test: {e}")
    import traceback
    traceback.print_exc()
