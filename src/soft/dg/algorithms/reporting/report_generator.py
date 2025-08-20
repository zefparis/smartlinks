"""
Générateur de rapports pour le DG autonome.

Ce module implémente des algorithmes pour générer des rapports périodiques
sur les performances du système, l'efficacité des algorithmes et les KPI business.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import pandas as pd
import numpy as np
from jinja2 import Environment, FileSystemLoader
import os
import importlib.util

from ...models.decision import Action, DecisionContext
from ..base import Algorithm, AlgorithmResult
from .report_sections import ReportSections

logger = logging.getLogger(__name__)

class ReportGenerator(Algorithm):
    """Génère des rapports périodiques sur l'état du système."""
    
    # Configuration par défaut
    DEFAULT_CONFIG = {
        "report_types": ["daily", "weekly", "monthly"],
        "report_formats": ["html", "json", "csv"],
        "retention_days": 90,
        "kpis": {
            "conversion_rate": {"target": 0.05, "min": 0.03},
            "revenue_per_click": {"target": 1.5, "min": 1.0},
            "system_uptime": {"target": 99.9, "min": 99.0},
            "error_rate": {"target": 0.01, "max": 0.05}
        },
        "sections": [
            "executive_summary",
            "performance_metrics",
            "anomalies",
            "recommendations",
            "system_health"
        ],
        "templates_dir": "templates/reports",
        "external_sections": {
            "executive_summary": "external_sections.executive_summary",
            "performance_metrics": "external_sections.performance_metrics",
            "anomalies": "external_sections.anomalies",
            "recommendations": "external_sections.recommendations",
            "system_health": "external_sections.system_health"
        }
    }
    
    @classmethod
    def get_name(cls) -> str:
        return "report_generator"
    
    def __init__(self):
        self._last_report = {}
        self._report_history = []
        self._sections = ReportSections()
        self._ensure_templates_dir()
        self._jinja_env = Environment(
            loader=FileSystemLoader(self.DEFAULT_CONFIG["templates_dir"]),
            autoescape=True
        )
    
    async def execute(self, context: DecisionContext, 
                     config: Optional[Dict[str, Any]] = None) -> AlgorithmResult:
        """Génère les rapports programmés."""
        # Fusion de la configuration par défaut avec celle fournie
        config = {**self.DEFAULT_CONFIG, **(config or {})}
        
        # Vérification des rapports à générer
        reports_to_generate = self._determine_reports_to_generate(config)
        
        if not reports_to_generate:
            return AlgorithmResult(
                algorithm_name=self.get_name(),
                confidence=0.0,
                recommended_actions=[]
            )
        
        # Génération des rapports
        actions = []
        report_data = {}
        
        for report_type in reports_to_generate:
            report = await self._generate_report(report_type, context, config)
            if report:
                report_data[report_type] = report
                
                # Création d'actions pour chaque format de sortie
                for fmt in config["report_formats"]:
                    action = self._create_report_action(report, report_type, fmt, config)
                    if action:
                        actions.append(action)
        
        # Mise à jour de l'historique
        self._update_report_history(report_data)
        
        return AlgorithmResult(
            algorithm_name=self.get_name(),
            confidence=0.9,  # Haute confiance pour ce type d'algorithme
            recommended_actions=actions,
            metadata={
                "reports_generated": list(report_data.keys()),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _ensure_templates_dir(self) -> None:
        """S'assure que le répertoire des modèles existe."""
        templates_dir = self.DEFAULT_CONFIG["templates_dir"]
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir, exist_ok=True)
            
            # Création d'un modèle par défaut si le répertoire était vide
            self._create_default_templates(templates_dir)
    
    def _create_default_templates(self, templates_dir: str) -> None:
        """Crée des modèles de rapport par défaut."""
        # Modèle HTML de base
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Rapport {{ report_type|title }} - {{ report_date }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1, h2 { color: #2c3e50; }
                .kpi { margin: 15px 0; padding: 10px; border-left: 4px solid #3498db; }
                .kpi.good { border-color: #2ecc71; }
                .kpi.warning { border-color: #f39c12; }
                .kpi.critical { border-color: #e74c3c; }
                table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>Rapport {{ report_type|title }}</h1>
            <p>Date: {{ report_date }}</p>
            
            <h2>Résumé Exécutif</h2>
            <div>{{ summary|safe }}</div>
            
            <h2>Indicateurs Clés de Performance</h2>
            {% for kpi in kpis %}
            <div class="kpi {{ kpi.status }}">
                <h3>{{ kpi.name }}</h3>
                <p>Valeur: {{ kpi.value }} (Cible: {{ kpi.target }})</p>
                <p>{{ kpi.interpretation }}</p>
            </div>
            {% endfor %}
            
            <h2>Recommandations</h2>
            <ul>
            {% for rec in recommendations %}
                <li>{{ rec }}</li>
            {% endfor %}
            </ul>
        </body>
        </html>
        """
        
        # Écriture du modèle HTML
        with open(os.path.join(templates_dir, "report.html.j2"), "w", encoding="utf-8") as f:
            f.write(html_template)
    
    def _determine_reports_to_generate(self, config: Dict[str, Any]) -> List[str]:
        """Détermine quels rapports doivent être générés."""
        now = datetime.utcnow()
        reports = []
        
        # Vérification des rapports journaliers (générés à minuit)
        if "daily" in config["report_types"]:
            last_daily = self._last_report.get("daily")
            if not last_daily or (now - last_daily).days >= 1:
                if now.hour == 0:  # Générer à minuit
                    reports.append("daily")
        
        # Vérification des rapports hebdomadaires (générés le lundi)
        if "weekly" in config["report_types"]:
            last_weekly = self._last_report.get("weekly")
            if not last_weekly or (now - last_weekly).days >= 7:
                if now.weekday() == 0 and now.hour == 0:  # Lundi à minuit
                    reports.append("weekly")
        
        # Vérification des rapports mensuels (générés le 1er du mois)
        if "monthly" in config["report_types"]:
            last_monthly = self._last_report.get("monthly")
            if not last_monthly or (now.year > last_monthly.year or 
                                  (now.year == last_monthly.year and 
                                   now.month > last_monthly.month)):
                if now.day == 1 and now.hour == 0:  # 1er du mois à minuit
                    reports.append("monthly")
        
        return reports
    
    async def _generate_report(self, report_type: str, 
                             context: DecisionContext,
                             config: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un rapport d'un type donné."""
        logger.info(f"Génération du rapport {report_type}...")
        
        # Récupération des données pour le rapport
        report_data = {
            "report_type": report_type,
            "report_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "period": self._get_report_period(report_type),
            "sections": {}
        }
        
        # Génération de chaque section du rapport
        for section in config["sections"]:
            section_method = getattr(self._sections, f"generate_{section}", None)
            if section_method and callable(section_method):
                try:
                    section_data = await section_method(report_type, context, config)
                    report_data["sections"][section] = section_data
                except Exception as e:
                    logger.error(f"Erreur lors de la génération de la section {section}: {e}")
                    report_data["sections"][section] = {
                        "error": f"Erreur lors de la génération: {str(e)}"
                    }
        
        # Mise à jour de la date du dernier rapport
        self._last_report[report_type] = datetime.utcnow()
        
        return report_data
    
    def _get_report_period(self, report_type: str) -> Dict[str, str]:
        """Définit la période couverte par le rapport."""
        now = datetime.utcnow()
        
        if report_type == "daily":
            start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif report_type == "weekly":
            start = (now - timedelta(days=now.weekday() + 7)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = (start + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
        else:  # monthly
            start = (now.replace(day=1) - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = start.replace(day=28) + timedelta(days=4)  # Pour gérer les mois de différentes longueurs
            end = (next_month - timedelta(days=next_month.day)).replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "timezone": "UTC"
        }
        
    def _update_report_history(self, report_data: Dict[str, Any]) -> None:
        """Met à jour l'historique des rapports."""
        for report_type, data in report_data.items():
            self._report_history.append({
                "type": report_type,
                "timestamp": data["report_date"],
                "data": data
            })
        
        # Nettoyage des anciens rapports
        cutoff = datetime.utcnow() - timedelta(days=self.DEFAULT_CONFIG["retention_days"])
        self._report_history = [
            r for r in self._report_history
            if datetime.fromisoformat(r["timestamp"].replace('Z', '+00:00')) > cutoff
        ]
        
    def _create_report_action(self, report_data: Dict[str, Any], 
                            report_type: str, 
                            fmt: str,
                            config: Dict[str, Any]) -> Optional[Action]:
        """Crée une action pour générer un rapport dans un format spécifique."""
        if fmt == "html":
            return self._create_html_report_action(report_data, report_type, config)
        elif fmt == "json":
            return self._create_json_report_action(report_data, report_type, config)
        elif fmt == "csv":
            return self._create_csv_report_action(report_data, report_type, config)
        
        return None
    
    def _create_html_report_action(self, report_data: Dict[str, Any],
                                 report_type: str,
                                 config: Dict[str, Any]) -> Optional[Action]:
        """Crée une action pour générer un rapport HTML."""
        try:
            template = self._jinja_env.get_template("report.html.j2")
            
            # Préparation des données pour le template
            context = {
                "report_type": report_type,
                "report_date": report_data["report_date"],
                "period": report_data["period"],
                "sections": report_data["sections"]
            }
            
            # Génération du HTML
            html_content = template.render(**context)
            
            # Création de l'action
            return Action(
                action_type="generate_report",
                params={
                    "report_type": report_type,
                    "format": "html",
                    "content": html_content,
                    "filename": f"report_{report_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html"
                },
                priority=50,
                description=f"Générer le rapport {report_type} au format HTML"
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport HTML: {e}")
            return None
    
    def _create_json_report_action(self, report_data: Dict[str, Any],
                                 report_type: str,
                                 config: Dict[str, Any]) -> Optional[Action]:
        """Crée une action pour générer un rapport JSON."""
        try:
            return Action(
                action_type="generate_report",
                params={
                    "report_type": report_type,
                    "format": "json",
                    "content": json.dumps(report_data, indent=2, ensure_ascii=False),
                    "filename": f"report_{report_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                },
                priority=50,
                description=f"Générer le rapport {report_type} au format JSON"
            )
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport JSON: {e}")
            return None
    
    def _create_csv_report_action(self, report_data: Dict[str, Any],
                                report_type: str,
                                config: Dict[str, Any]) -> Optional[Action]:
        """Crée une action pour générer un rapport CSV."""
        try:
            # Conversion des données en format plat pour le CSV
            flat_data = self._flatten_report_data(report_data)
            
            # Création d'un DataFrame pandas
            df = pd.DataFrame([flat_data])
            
            # Génération du contenu CSV
            csv_content = df.to_csv(index=False, encoding='utf-8')
            
            return Action(
                action_type="generate_report",
                params={
                    "report_type": report_type,
                    "format": "csv",
                    "content": csv_content,
                    "filename": f"report_{report_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
                },
                priority=50,
                description=f"Générer le rapport {report_type} au format CSV"
            )
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport CSV: {e}")
            return None
    
    def _flatten_report_data(self, data: Dict[str, Any], prefix: str = '') -> Dict[str, Any]:
        """Aplatit les données du rapport pour le format CSV."""
        items = {}
        for key, value in data.items():
            new_key = f"{prefix}_{key}" if prefix else key
            
            if isinstance(value, dict):
                items.update(self._flatten_report_data(value, new_key))
            elif isinstance(value, (list, tuple)):
                # Pour les listes, on les convertit en chaînes JSON
                items[new_key] = json.dumps(value, ensure_ascii=False)
            else:
                items[new_key] = value
                
        return items
