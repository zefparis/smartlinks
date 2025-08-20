"""
Module de base pour les algorithmes du DG autonome.

Définit les interfaces et classes de base pour tous les algorithmes.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from ...models.decision import Action

@dataclass
class AlgorithmResult:
    """Résultat de l'exécution d'un algorithme."""
    algorithm_name: str
    confidence: float = 0.0
    recommended_actions: List[Action] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

class Algorithm(ABC):
    """Classe de base pour tous les algorithmes du DG autonome.
    
    Les algorithmes doivent hériter de cette classe et implémenter la méthode execute().
    """
    
    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """Retourne le nom unique de l'algorithme.
        
        Returns:
            str: Nom unique de l'algorithme
        """
        pass
    
    @abstractmethod
    async def execute(self, context: 'DecisionContext', 
                     config: Dict[str, Any]) -> AlgorithmResult:
        """Exécute l'algorithme sur le contexte donné.
        
        Args:
            context: Contexte de décision actuel
            config: Configuration spécifique à l'algorithme
            
        Returns:
            AlgorithmResult: Résultat de l'exécution
        """
        pass
    
    def _create_action(self, action_type: str, 
                      params: Dict[str, Any] = None,
                      priority: int = 0,
                      description: str = "") -> Action:
        """Crée une nouvelle action recommandée.
        
        Args:
            action_type: Type d'action (ex: 'update_config', 'block_traffic')
            params: Paramètres de l'action
            priority: Priorité (plus élevé = plus important)
            description: Description lisible par un humain
            
        Returns:
            Action: Nouvelle action recommandée
        """
        return Action(
            action_type=action_type,
            params=params or {},
            priority=priority,
            description=description,
            source_algorithm=self.get_name()
        )
    
    def _log(self, message: str, level: str = "info", **kwargs) -> None:
        """Journalise un message avec des métadonnées.
        
        Args:
            message: Message à journaliser
            level: Niveau de log (debug, info, warning, error, critical)
            **kwargs: Métadonnées supplémentaires
        """
        from ...monitoring.logger import get_dg_logger
        
        logger = get_dg_logger()
        log_method = getattr(logger, level.lower(), logger.info)
        
        log_message = f"[{self.get_name()}] {message}"
        log_method(log_message, extra={"algorithm": self.get_name(), **kwargs})


class CompositeAlgorithm(Algorithm):
    """Algorithme composite qui exécute plusieurs algorithmes en parallèle.
    
    Combine les résultats de plusieurs algorithmes en un seul résultat.
    """
    
    def __init__(self, algorithms: List[Algorithm] = None):
        """Initialise le composite avec une liste d'algorithmes."""
        self.algorithms = algorithms or []
    
    @classmethod
    def get_name(cls) -> str:
        return "composite_algorithm"
    
    async def execute(self, context: 'DecisionContext', 
                     config: Dict[str, Any]) -> AlgorithmResult:
        """Exécute tous les algorithmes et combine leurs résultats."""
        import asyncio
        from typing import List, Tuple
        
        # Exécution en parallèle de tous les algorithmes
        tasks = [algo.execute(context, config) for algo in self.algorithms]
        results: List[AlgorithmResult] = await asyncio.gather(*tasks)
        
        # Agrégation des résultats
        return self._aggregate_results(results)
    
    def _aggregate_results(self, results: List[AlgorithmResult]) -> AlgorithmResult:
        """Combine les résultats de plusieurs algorithmes."""
        # Par défaut, on prend l'action avec la plus haute confiance
        best_result = max(results, key=lambda r: r.confidence, 
                         default=AlgorithmResult(algorithm_name="composite"))
        
        # On pourrait implémenter une logique plus sophistiquée ici
        return best_result
    
    def add_algorithm(self, algorithm: Algorithm) -> None:
        """Ajoute un algorithme au composite."""
        self.algorithms.append(algorithm)
    
    def remove_algorithm(self, algorithm_name: str) -> bool:
        """Supprime un algorithme du composite."""
        initial_count = len(self.algorithms)
        self.algorithms = [a for a in self.algorithms 
                          if a.get_name() != algorithm_name]
        return len(self.algorithms) < initial_count
