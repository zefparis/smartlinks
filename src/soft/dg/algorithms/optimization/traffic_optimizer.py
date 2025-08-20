"""
Optimiseur de trafic pour le DG autonome.

Ce module implémente des algorithmes pour optimiser l'allocation du trafic
entre différentes offres, créateurs et segments en fonction des performances.
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from scipy.optimize import linear_sum_assignment

from ...models.decision import Action, DecisionContext
from ..base import Algorithm, AlgorithmResult

logger = logging.getLogger(__name__)

class TrafficOptimizer(Algorithm):
    """Optimise l'allocation du trafic pour maximiser les conversions."""
    
    # Configuration par défaut
    DEFAULT_CONFIG = {
        "min_traffic_per_offer": 0.05,  # 5% de trafic minimum par offre
        "max_traffic_shift": 0.2,  # 20% de changement max par itération
        "min_conversions_for_optimization": 10,  # Nombre minimum de conversions pour optimiser
        "optimization_interval_hours": 4,  # Fréquence d'optimisation
        "segment_weights": {  # Poids des segments pour l'optimisation
            "geo": 0.4,
            "device": 0.3,
            "source": 0.3
        },
        "exploration_rate": 0.1  # Pourcentage de trafic à allouer à l'exploration
    }
    
    @classmethod
    def get_name(cls) -> str:
        return "traffic_optimizer"
    
    def __init__(self):
        self._last_optimization = None
        self._current_allocation = {}
        self._performance_history = []
    
    async def execute(self, context: DecisionContext, 
                     config: Optional[Dict[str, Any]] = None) -> AlgorithmResult:
        """Exécute l'optimisation du trafic."""
        # Fusion de la configuration par défaut avec celle fournie
        config = {**self.DEFAULT_CONFIG, **(config or {})}
        
        # Vérification si c'est le moment d'optimiser
        if not self._should_optimize(context, config):
            return AlgorithmResult(
                algorithm_name=self.get_name(),
                confidence=0.0,
                recommended_actions=[]
            )
        
        # Extraction des données de performance
        performance_data = self._extract_performance_data(context)
        
        # Vérification si on a assez de données pour optimiser
        if not self._has_sufficient_data(performance_data, config):
            logger.info("Données insuffisantes pour l'optimisation")
            return AlgorithmResult(
                algorithm_name=self.get_name(),
                confidence=0.0,
                recommended_actions=[]
            )
        
        # Calcul de la nouvelle allocation optimale
        new_allocation, confidence = self._calculate_optimal_allocation(
            performance_data, 
            config
        )
        
        # Mise à jour de l'historique
        self._update_history(performance_data, new_allocation)
        
        # Création des actions recommandées
        actions = self._create_allocation_actions(
            new_allocation, 
            self._current_allocation,
            config
        )
        
        # Mise à jour de l'allocation courante
        self._current_allocation = new_allocation
        self._last_optimization = datetime.utcnow()
        
        return AlgorithmResult(
            algorithm_name=self.get_name(),
            confidence=confidence,
            recommended_actions=actions,
            metadata={
                "previous_allocation": self._current_allocation,
                "new_allocation": new_allocation,
                "performance_data": performance_data,
                "optimization_timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _should_optimize(self, context: DecisionContext, 
                        config: Dict[str, Any]) -> bool:
        """Détermine si une optimisation doit être effectuée."""
        # Première exécution
        if self._last_optimization is None:
            return True
        
        # Vérification de l'intervalle d'optimisation
        time_since_last = (datetime.utcnow() - self._last_optimization).total_seconds()
        min_interval = config["optimization_interval_hours"] * 3600
        
        return time_since_last >= min_interval
    
    def _extract_performance_data(self, context: DecisionContext) -> Dict[str, Any]:
        """Extrait les données de performance du contexte."""
        # Dans une implémentation réelle, on irait chercher ces données en base
        # Pour l'exemple, on utilise des données factices
        
        # Exemple de structure de données de performance
        return {
            "offers": [
                {
                    "offer_id": "offer_a",
                    "impressions": 1000,
                    "clicks": 100,
                    "conversions": 10,
                    "revenue": 500.0,
                    "segments": {
                        "geo:FR": {"impressions": 400, "clicks": 45, "conversions": 5},
                        "geo:US": {"impressions": 300, "clicks": 30, "conversions": 3},
                        "device:mobile": {"impressions": 600, "clicks": 55, "conversions": 6},
                        "device:desktop": {"impressions": 400, "clicks": 45, "conversions": 4}
                    }
                },
                {
                    "offer_id": "offer_b",
                    "impressions": 800,
                    "clicks": 120,
                    "conversions": 18,
                    "revenue": 720.0,
                    "segments": {
                        "geo:FR": {"impressions": 300, "clicks": 50, "conversions": 8},
                        "geo:US": {"impressions": 200, "clicks": 40, "conversions": 6},
                        "device:mobile": {"impressions": 500, "clicks": 80, "conversions": 12},
                        "device:desktop": {"impressions": 300, "clicks": 40, "conversions": 6}
                    }
                }
            ],
            "time_period": {
                "start": (datetime.utcnow() - timedelta(hours=24)).isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "total_impressions": 1800,
            "total_clicks": 220,
            "total_conversions": 28,
            "total_revenue": 1220.0
        }
    
    def _has_sufficient_data(self, performance_data: Dict[str, Any],
                           config: Dict[str, Any]) -> bool:
        """Vérifie si les données sont suffisantes pour l'optimisation."""
        if not performance_data.get("offers"):
            return False
        
        # Vérification du nombre minimum de conversions
        if performance_data.get("total_conversions", 0) < config["min_conversions_for_optimization"]:
            return False
        
        return True
    
    def _calculate_optimal_allocation(self, performance_data: Dict[str, Any],
                                    config: Dict[str, Any]) -> Tuple[Dict[str, float], float]:
        """Calcule la nouvelle allocation optimale du trafic."""
        offers = performance_data["offers"]
        total_impressions = performance_data["total_impressions"]
        
        # Calcul des scores de performance pour chaque offre
        offer_scores = {}
        for offer in offers:
            # Score basé sur le taux de conversion et le revenu par impression
            conv_rate = offer["conversions"] / max(offer["clicks"], 1)
            revenue_per_impression = offer["revenue"] / max(offer["impressions"], 1)
            
            # Score composite (pondéré)
            score = 0.7 * conv_rate + 0.3 * revenue_per_impression
            offer_scores[offer["offer_id"]] = score
        
        # Normalisation des scores
        total_score = sum(offer_scores.values())
        if total_score == 0:
            # Égalité si aucun score
            allocation = {offer_id: 1.0 / len(offer_scores) 
                         for offer_id in offer_scores}
            return allocation, 0.5  # Confiance faible
        
        # Calcul de l'allocation proportionnelle aux scores
        allocation = {}
        for offer_id, score in offer_scores.items():
            # Application d'un minimum de trafic pour chaque offre
            min_traffic = config["min_traffic_per_offer"]
            normalized = max(score / total_score, min_traffic)
            allocation[offer_id] = normalized
        
        # Normalisation pour que la somme fasse 1
        total = sum(allocation.values())
        allocation = {k: v / total for k, v in allocation.items()}
        
        # Calcul de la confiance basée sur la variance des performances
        confidence = self._calculate_confidence(offer_scores.values())
        
        return allocation, confidence
    
    def _calculate_confidence(self, scores: List[float]) -> float:
        """Calcule la confiance dans l'allocation basée sur les scores."""
        if not scores or len(scores) < 2:
            return 0.5
        
        # Plus la variance est élevée, plus on est confiant dans la différence
        # entre les offres
        variance = np.var(scores)
        confidence = min(1.0, variance * 10)  # Ajustement de l'échelle
        
        return max(0.1, confidence)  # Minimum 10% de confiance
    
    def _update_history(self, performance_data: Dict[str, Any],
                       new_allocation: Dict[str, float]) -> None:
        """Met à jour l'historique des performances et allocations."""
        self._performance_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "performance": performance_data,
            "allocation": new_allocation
        })
        
        # Limite de l'historique
        if len(self._performance_history) > 30:  # Garder les 30 derniers jours
            self._performance_history = self._performance_history[-30:]
    
    def _create_allocation_actions(self, new_allocation: Dict[str, float],
                                 current_allocation: Dict[str, float],
                                 config: Dict[str, Any]) -> List[Action]:
        """Crée les actions pour mettre à jour l'allocation du trafic."""
        actions = []
        
        # Si c'est la première allocation, on l'applique complètement
        if not current_allocation:
            return [
                Action(
                    action_type="update_traffic_allocation",
                    params={
                        "allocation": new_allocation,
                        "reason": "Initial traffic allocation"
                    },
                    priority=80,
                    description=f"Mise à jour de l'allocation du trafic: {new_allocation}"
                )
            ]
        
        # Sinon, on calcule les changements nécessaires
        changes = {}
        max_shift = config["max_traffic_shift"]
        
        for offer_id, new_share in new_allocation.items():
            current_share = current_allocation.get(offer_id, 0.0)
            
            # Application de la limite de changement maximal
            change = new_share - current_share
            if abs(change) > max_shift:
                change = max_shift if change > 0 else -max_shift
            
            changes[offer_id] = current_share + change
        
        # Normalisation pour que la somme fasse 1
        total = sum(changes.values())
        normalized_changes = {k: v / total for k, v in changes.items()}
        
        # Création de l'action
        actions.append(
            Action(
                action_type="update_traffic_allocation",
                params={
                    "allocation": normalized_changes,
                    "reason": "Optimisation périodique du trafic"
                },
                priority=70,
                description=f"Ajustement de l'allocation du trafic vers {normalized_changes}"
            )
        )
        
        return actions
