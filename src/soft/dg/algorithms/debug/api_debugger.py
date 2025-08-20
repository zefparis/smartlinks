"""
Débogueur d'API pour le DG autonome.

Ce module implémente des algorithmes pour détecter et corriger automatiquement
les problèmes courants dans les API, comme les erreurs 5xx, les temps de réponse
élevés, ou les fuites de mémoire.
"""
import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import psutil
import requests

from ...models.decision import Action, DecisionContext
from ..base import Algorithm, AlgorithmResult

logger = logging.getLogger(__name__)

class APIDebugger(Algorithm):
    """Détecte et corrige les problèmes d'API de manière autonome."""
    
    # Configuration par défaut
    DEFAULT_CONFIG = {
        "max_response_time_ms": 500,  # Temps de réponse maximum acceptable (ms)
        "error_rate_threshold": 0.01,  # Taux d'erreur maximum (1%)
        "memory_threshold_mb": 500,    # Utilisation mémoire max avant alerte (MB)
        "cpu_threshold_percent": 80,   # Utilisation CPU max avant alerte (%)
        "endpoints_to_monitor": [
            "/api/clicks",
            "/api/conversions",
            "/api/offers"
        ],
        "health_check_interval_sec": 60,  # Intervalle entre les vérifications
        "auto_rollback_on_failure": True  # Annulation automatique des changements problématiques
    }
    
    @classmethod
    def get_name(cls) -> str:
        return "api_debugger"
    
    def __init__(self):
        self._last_check = {}
        self._error_counts = {}
        self._response_times = {}
        self._rollback_stack = []
        self._last_rollback = None
    
    async def execute(self, context: DecisionContext, 
                     config: Optional[Dict[str, Any]] = None) -> AlgorithmResult:
        """Exécute la détection et la correction des problèmes d'API."""
        # Fusion de la configuration par défaut avec celle fournie
        config = {**self.DEFAULT_CONFIG, **(config or {})}
        
        # Vérification des ressources système
        system_issues = await self._check_system_health(config)
        
        # Vérification des endpoints d'API
        api_issues = await self._check_api_endpoints(config)
        
        # Agrégation des problèmes
        all_issues = system_issues + api_issues
        
        # Création des actions recommandées
        actions = []
        for issue in all_issues:
            action = self._create_remediation_action(issue, config)
            if action:
                actions.append(action)
        
        # Vérification des rollbacks nécessaires
        if config["auto_rollback_on_failure"]:
            rollback_actions = await self._check_for_rollback()
            actions.extend(rollback_actions)
        
        # Calcul de la confiance globale
        confidence = 0.8 if all_issues else 0.95  # Haute confiance si pas de problèmes
        
        return AlgorithmResult(
            algorithm_name=self.get_name(),
            confidence=confidence,
            recommended_actions=actions,
            metadata={
                "issues_found": len(all_issues),
                "issues_details": all_issues,
                "last_check": datetime.utcnow().isoformat()
            }
        )
    
    async def _check_system_health(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Vérifie la santé du système (mémoire, CPU, etc.)."""
        issues = []
        
        # Vérification de la mémoire
        memory_mb = psutil.virtual_memory().used / (1024 * 1024)
        if memory_mb > config["memory_threshold_mb"]:
            issues.append({
                "type": "high_memory_usage",
                "current_mb": round(memory_mb, 2),
                "threshold_mb": config["memory_threshold_mb"],
                "severity": "high"
            })
        
        # Vérification du CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > config["cpu_threshold_percent"]:
            issues.append({
                "type": "high_cpu_usage",
                "current_percent": round(cpu_percent, 2),
                "threshold_percent": config["cpu_threshold_percent"],
                "severity": "high"
            })
        
        return issues
    
    async def _check_api_endpoints(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Vérifie la santé des endpoints d'API."""
        issues = []
        base_url = "http://localhost:8000"  # À remplacer par la configuration réelle
        
        for endpoint in config["endpoints_to_monitor"]:
            url = f"{base_url}{endpoint}"
            
            try:
                # Mesure du temps de réponse
                start_time = time.time()
                response = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: requests.get(url, timeout=5)
                )
                response_time_ms = (time.time() - start_time) * 1000
                
                # Enregistrement des métriques
                self._record_metrics(endpoint, response.status_code, response_time_ms)
                
                # Vérification du temps de réponse
                if response_time_ms > config["max_response_time_ms"]:
                    issues.append({
                        "type": "high_response_time",
                        "endpoint": endpoint,
                        "response_time_ms": round(response_time_ms, 2),
                        "threshold_ms": config["max_response_time_ms"],
                        "status_code": response.status_code,
                        "severity": "medium"
                    })
                
                # Vérification des codes d'erreur
                if response.status_code >= 500:
                    issues.append({
                        "type": "server_error",
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "severity": "critical"
                    })
                
            except Exception as e:
                # Erreur de connexion ou timeout
                self._record_error(endpoint)
                
                issues.append({
                    "type": "connection_error",
                    "endpoint": endpoint,
                    "error": str(e),
                    "severity": "critical"
                })
        
        # Vérification du taux d'erreur global
        error_rate = self._calculate_error_rate()
        if error_rate > config["error_rate_threshold"]:
            issues.append({
                "type": "high_error_rate",
                "current_rate": error_rate,
                "threshold": config["error_rate_threshold"],
                "severity": "high"
            })
        
        return issues
    
    def _record_metrics(self, endpoint: str, status_code: int, response_time_ms: float) -> None:
        """Enregistre les métriques de performance pour un endpoint."""
        now = time.time()
        
        # Initialisation des compteurs si nécessaire
        if endpoint not in self._response_times:
            self._response_times[endpoint] = []
            self._error_counts[endpoint] = 0
        
        # Enregistrement du temps de réponse
        self._response_times[endpoint].append((now, response_time_ms))
        
        # Nettoyage des anciennes entrées (garder les 5 dernières minutes)
        cutoff = now - 300
        self._response_times[endpoint] = [
            (ts, rt) for ts, rt in self._response_times[endpoint] 
            if ts > cutoff
        ]
        
        # Comptage des erreurs
        if status_code >= 400:
            self._error_counts[endpoint] += 1
    
    def _record_error(self, endpoint: str) -> None:
        """Enregistre une erreur pour un endpoint."""
        if endpoint not in self._error_counts:
            self._error_counts[endpoint] = 0
        self._error_counts[endpoint] += 1
    
    def _calculate_error_rate(self) -> float:
        """Calcule le taux d'erreur global."""
        total_requests = sum(len(times) for times in self._response_times.values())
        total_errors = sum(self._error_counts.values())
        
        if total_requests == 0:
            return 0.0
            
        return total_errors / total_requests
    
    def _create_remediation_action(self, issue: Dict[str, Any], 
                                 config: Dict[str, Any]) -> Optional[Action]:
        """Crée une action de correction pour un problème détecté."""
        issue_type = issue.get("type")
        
        if issue_type == "high_memory_usage":
            return Action(
                action_type="restart_service",
                params={
                    "service": "api",
                    "reason": f"Utilisation mémoire élevée: {issue['current_mb']:.2f}MB"
                },
                priority=90,
                description="Redémarrer le service API pour libérer de la mémoire"
            )
        
        elif issue_type == "high_cpu_usage":
            return Action(
                action_type="scale_service",
                params={
                    "service": "api",
                    "action": "scale_up",
                    "reason": f"Utilisation CPU élevée: {issue['current_percent']}%"
                },
                priority=80,
                description="Augmenter le nombre d'instances du service API"
            )
        
        elif issue_type == "high_response_time":
            return Action(
                action_type="optimize_endpoint",
                params={
                    "endpoint": issue["endpoint"],
                    "current_ms": issue["response_time_ms"],
                    "threshold_ms": issue["threshold_ms"]
                },
                priority=70,
                description=f"Optimiser les performances de l'endpoint {issue['endpoint']}"
            )
        
        elif issue_type in ["server_error", "connection_error"]:
            return Action(
                action_type="alert_team",
                params={
                    "message": f"Problème critique avec {issue['endpoint']}: {issue.get('error', 'Erreur serveur')}",
                    "severity": "critical",
                    "endpoint": issue["endpoint"]
                },
                priority=100,
                description=f"Alerter l'équipe à propos du problème avec {issue['endpoint']}"
            )
        
        elif issue_type == "high_error_rate":
            return Action(
                action_type="enable_circuit_breaker",
                params={
                    "error_rate": issue["current_rate"],
                    "threshold": issue["threshold"]
                },
                priority=90,
                description="Activer le circuit breaker en raison d'un taux d'erreur élevé"
            )
        
        return None
    
    async def _check_for_rollback(self) -> List[Action]:
        """Vérifie si un rollback est nécessaire."""
        # Dans une implémentation réelle, on vérifierait si les dernières actions
        # ont entraîné des problèmes et on proposerait un rollback si nécessaire
        
        # Pour l'exemple, on ne retourne pas de rollback
        return []
    
    def _push_to_rollback_stack(self, action: Action) -> None:
        """Ajoute une action à la pile de rollback."""
        self._rollback_stack.append({
            "action": action,
            "timestamp": datetime.utcnow(),
            "rolled_back": False
        })
        
        # Limite de la taille de la pile
        if len(self._rollback_stack) > 50:
            self._rollback_stack = self._rollback_stack[-50:]
    
    async def _execute_rollback(self) -> bool:
        """Exécute un rollback des dernières actions."""
        if not self._rollback_stack:
            return False
        
        # On ne rollback pas trop fréquemment
        if (self._last_rollback and 
            (datetime.utcnow() - self._last_rollback) < timedelta(minutes=5)):
            return False
        
        # On prend la dernière action non rollbackée
        for item in reversed(self._rollback_stack):
            if not item["rolled_back"]:
                # Implémentation du rollback spécifique à l'action
                # (à adapter selon les besoins)
                try:
                    # Exemple de logique de rollback
                    action = item["action"]
                    logger.info(f"Rolling back action: {action.action_type}")
                    
                    # Marquer comme rollbacké
                    item["rolled_back"] = True
                    self._last_rollback = datetime.utcnow()
                    
                    return True
                except Exception as e:
                    logger.error(f"Erreur lors du rollback: {e}")
                    return False
        
        return False
