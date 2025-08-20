# Système de Génération de Rapports du DG Autonome

## Aperçu

Le système de génération de rapports est un composant clé du DG autonome qui permet de produire des rapports périodiques sur l'état du système, les performances et les anomalies détectées.

## Architecture

```
src/soft/dg/algorithms/reporting/
├── __init__.py          # Exporte les classes principales
├── report_generator.py  # Générateur principal de rapports
└── report_sections.py   # Définition des sections de rapport
```

## Composants Principaux

### 1. ReportGenerator

Classe principale qui gère :
- La planification des rapports (quotidiens, hebdomadaires, mensuels)
- L'orchestration de la génération des sections
- L'export dans différents formats (HTML, JSON, CSV)
- La gestion de l'historique des rapports

### 2. ReportSections

Conteneur pour les différentes sections d'un rapport :
- Résumé exécutif
- Métriques de performance
- Anomalies détectées
- Recommandations
- État de santé du système

## Configuration

La configuration par défaut inclut :
- Types de rapports : journalier, hebdomadaire, mensuel
- Formats de sortie : HTML, JSON, CSV
- Période de rétention : 90 jours
- Seuils pour les KPI

## Utilisation

```python
from dg.algorithms.reporting import ReportGenerator

# Création d'une instance
generator = ReportGenerator()

# Génération d'un rapport
result = await generator.execute(context, config)
```

## Personnalisation

Pour ajouter une nouvelle section :
1. Créer une méthode `generate_<nom_section>` dans `ReportSections`
2. L'ajouter à la liste des sections dans la configuration

## Formats de Sortie

### HTML
Génère un rapport visuel avec mise en page riche.

### JSON
Exporte les données brutes pour traitement ultérieur.

### CSV
Exporte les données dans un format tabulaire pour analyse.

## Bonnes Pratiques

- Toujours gérer les erreurs dans les générateurs de sections
- Documenter les nouvelles sections
- Tester avec différents jeux de données
- Surveiller l'utilisation des ressources lors de la génération de rapports volumineux
