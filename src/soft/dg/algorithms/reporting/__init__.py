"""
Package pour la génération de rapports dans le DG autonome.

Ce package contient les classes et fonctions nécessaires pour générer des rapports
sur les performances du système, les anomalies détectées et les recommandations.
"""
from .report_generator import ReportGenerator
from .report_sections import ReportSections

__all__ = [
    'ReportGenerator',
    'ReportSections'
]
