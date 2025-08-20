"""Test simple pour le générateur de rapports."""
import sys
import os
from datetime import datetime, timedelta

# Ajoute le répertoire src au chemin Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

def test_report_generator():
    """Teste la création d'une instance du générateur de rapports."""
    try:
        from soft.dg.algorithms.reporting import ReportGenerator
        generator = ReportGenerator()
        print("✅ Le générateur de rapports a été importé avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'importation du générateur de rapports: {e}")
        return False

def test_report_sections():
    """Teste la création d'une instance des sections de rapport."""
    try:
        from soft.dg.algorithms.reporting.report_sections import ReportSections
        sections = ReportSections()
        print("✅ Les sections de rapport ont été importées avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'importation des sections de rapport: {e}")
        return False

def test_generate_report():
    """Teste la génération d'un rapport simple."""
    try:
        from soft.dg.algorithms.reporting import ReportGenerator
        from soft.dg.models.decision import DecisionContext
        
        # Crée un contexte de décision de test
        context = DecisionContext(
            request_id="test-123",
            timestamp=datetime.utcnow(),
            metadata={"test": "data"}
        )
        
        # Configuration de test
        config = {
            "report_types": ["daily"],
            "report_formats": ["html"],
            "sections": ["executive_summary"],
            "templates_dir": "templates",
            "kpi_targets": {
                "conversion_rate": {"target": 0.04, "min": 0.03},
                "click_through_rate": {"target": 0.10, "min": 0.08},
                "revenue": {"target": 1000.0, "min": 800.0}
            }
        }
        
        # Crée et exécute le générateur
        generator = ReportGenerator()
        
        # Teste la génération du rapport
        import asyncio
        
        async def run_test():
            result = await generator.execute(context, config)
            if result and hasattr(result, 'actions') and result.actions:
                print(f"✅ Rapport généré avec succès. Actions: {len(result.actions)}")
                return True
            else:
                print("❌ Échec de la génération du rapport")
                return False
        
        return asyncio.run(run_test())
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du rapport: {e}")
        return False

def main():
    """Fonction principale pour exécuter les tests."""
    print("=== Démarrage des tests du générateur de rapports ===\n")
    
    # Exécute les tests
    tests = [
        ("Test d'importation du générateur", test_report_generator),
        ("Test d'importation des sections", test_report_sections),
        ("Test de génération de rapport", test_generate_report)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n=== {name} ===")
        result = test_func()
        results.append((name, result))
    
    # Affiche le résumé
    print("\n=== Résumé des tests ===")
    for name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"{status} - {name}")
    
    # Retourne le code de sortie approprié
    if all(result for _, result in results):
        print("\nTous les tests ont réussi !")
        return 0
    else:
        print("\nCertains tests ont échoué.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
