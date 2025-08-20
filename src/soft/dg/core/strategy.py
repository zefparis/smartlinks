"""
Moteur de stratégie du DG autonome.

Gère la sélection et l'exécution des algorithmes en fonction du contexte.
"""
from typing import Dict, List, Any, Optional, Type, TypeVar, Generic
from dataclasses import dataclass, field
import asyncio
import logging
from datetime import datetime
import inspect

from ..models.decision import DecisionContext, Action, Decision
from ..algorithms.base import Algorithm, AlgorithmResult

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Algorithm)

@dataclass
class RegisteredAlgorithm:
    """Représente un algorithme enregistré dans le moteur."""
    algorithm_class: Type[Algorithm]
    instance: Optional[Algorithm] = None
    config: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    last_executed: Optional[datetime] = None
    execution_count: int = 0

class StrategyEngine:
    """Moteur de stratégie pour la sélection d'algorithmes."""
    
    def __init__(self):
        self.algorithms: Dict[str, RegisteredAlgorithm] = {}
        self.execution_lock = asyncio.Lock()
        self.context_history: List[DecisionContext] = []
        self.max_history_size = 1000
    
    def register_algorithm(self, algorithm_class: Type[Algorithm], 
                         config: Optional[Dict[str, Any]] = None) -> None:
        """Enregistre un nouvel algorithme.
        
        Args:
            algorithm_class: Classe de l'algorithme (héritant de Algorithm)
            config: Configuration spécifique à l'algorithme
        """
        if not inspect.isclass(algorithm_class) or not issubclass(algorithm_class, Algorithm):
            raise ValueError("L'algorithme doit être une sous-classe de Algorithm")
            
        algo_name = algorithm_class.get_name()
        self.algorithms[algo_name] = RegisteredAlgorithm(
            algorithm_class=algorithm_class,
            config=config or {}
        )
        logger.info(f"Algorithme enregistré: {algo_name}")
    
    async def activate_algorithm(self, algorithm_name: str) -> bool:
        """Active un algorithme.
        
        Args:
            algorithm_name: Nom de l'algorithme à activer
            
        Returns:
            bool: True si l'activation a réussi
        """
        if algorithm_name not in self.algorithms:
            logger.warning(f"Tentative d'activer un algorithme inconnu: {algorithm_name}")
            return False
            
        async with self.execution_lock:
            self.algorithms[algorithm_name].active = True
            logger.info(f"Algorithme activé: {algorithm_name}")
            return True
    
    async def deactivate_algorithm(self, algorithm_name: str) -> bool:
        """Désactive un algorithme.
        
        Args:
            algorithm_name: Nom de l'algorithme à désactiver
            
        Returns:
            bool: True si la désactivation a réussi
        """
        if algorithm_name not in self.algorithms:
            logger.warning(f"Tentative de désactiver un algorithme inconnu: {algorithm_name}")
            return False
            
        async with self.execution_lock:
            self.algorithms[algorithm_name].active = False
            logger.info(f"Algorithme désactivé: {algorithm_name}")
            return True
    
    async def update_algorithm_config(self, algorithm_name: str, 
                                    config: Dict[str, Any]) -> bool:
        """Met à jour la configuration d'un algorithme.
        
        Args:
            algorithm_name: Nom de l'algorithme
            config: Nouvelles valeurs de configuration
            
        Returns:
            bool: True si la mise à jour a réussi
        """
        if algorithm_name not in self.algorithms:
            logger.warning(f"Tentative de configurer un algorithme inconnu: {algorithm_name}")
            return False
            
        async with self.execution_lock:
            self.algorithms[algorithm_name].config.update(config)
            logger.info(f"Configuration mise à jour pour l'algorithme: {algorithm_name}")
            return True
    
    async def analyze(self, context: DecisionContext) -> DecisionContext:
        """Analyse le contexte et renvoie des actions recommandées.
        
        Args:
            context: Contexte d'analyse
            
        Returns:
            DecisionContext: Contexte mis à jour avec les actions recommandées
        """
        # Ajout du contexte à l'historique
        self._add_to_history(context)
        
        # Exécution des algorithmes actifs
        results = await self._execute_algorithms(context)
        
        # Agrégation des résultats
        return self._aggregate_results(context, results)
    
    async def _execute_algorithms(self, context: DecisionContext) -> Dict[str, AlgorithmResult]:
        """Exécute les algorithmes actifs."""
        results = {}
        
        # Filtrer les algorithmes actifs
        active_algorithms = [
            (name, algo) for name, algo in self.algorithms.items() 
            if algo.active
        ]
        
        # Exécution en parallèle des algorithmes
        tasks = []
        for algo_name, registered_algo in active_algorithms:
            tasks.append(self._execute_single_algorithm(algo_name, registered_algo, context))
        
        # Attendre la fin de toutes les exécutions
        algo_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Traitement des résultats
        for algo_name, result in zip((a[0] for a in active_algorithms), algo_results):
            if isinstance(result, Exception):
                logger.error(f"Erreur lors de l'exécution de l'algorithme {algo_name}: {result}")
            else:
                results[algo_name] = result
        
        return results
    
    async def _execute_single_algorithm(self, algo_name: str, 
                                      registered_algo: RegisteredAlgorithm,
                                      context: DecisionContext) -> AlgorithmResult:
        """Exécute un seul algorithme et gère les erreurs."""
        try:
            # Création de l'instance si nécessaire
            if registered_algo.instance is None:
                registered_algo.instance = registered_algo.algorithm_class()
            
            # Exécution de l'algorithme
            start_time = datetime.utcnow()
            result = await registered_algo.instance.execute(context, registered_algo.config)
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Mise à jour des métriques
            registered_algo.last_executed = datetime.utcnow()
            registered_algo.execution_count += 1
            
            logger.debug(
                f"Algorithme {algo_name} exécuté en {execution_time:.3f}s "
                f"(score: {result.confidence:.2f})"
            )
            
            return result
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'exécution de l'algorithme {algo_name}")
            raise
    
    def _aggregate_results(self, context: DecisionContext, 
                          results: Dict[str, AlgorithmResult]) -> DecisionContext:
        """Agrège les résultats des différents algorithmes."""
        # Ici, on pourrait implémenter une logique plus sophistiquée pour
        # combiner les résultats de plusieurs algorithmes
        
        # Pour l'instant, on prend simplement la meilleure décision
        # basée sur le score de confiance
        best_result = None
        best_confidence = -1
        
        for algo_name, result in results.items():
            if result.confidence > best_confidence and result.recommended_actions:
                best_result = result
                best_confidence = result.confidence
        
        # Mise à jour du contexte avec les actions recommandées
        if best_result:
            context.recommended_actions = best_result.recommended_actions
            context.confidence = best_confidence
            context.metadata["best_algorithm"] = best_result.algorithm_name
        
        return context
    
    def _add_to_history(self, context: DecisionContext) -> None:
        """Ajoute le contexte à l'historique."""
        self.context_history.append(context)
        
        # Limite de la taille de l'historique
        if len(self.context_history) > self.max_history_size:
            self.context_history = self.context_history[-self.max_history_size:]
    
    def get_algorithm_status(self) -> Dict[str, Dict[str, Any]]:
        """Retourne l'état de tous les algorithmes enregistrés."""
        status = {}
        
        for name, algo in self.algorithms.items():
            status[name] = {
                "active": algo.active,
                "last_executed": algo.last_executed.isoformat() if algo.last_executed else None,
                "execution_count": algo.execution_count,
                "config": algo.config
            }
        
        return status
    
    def get_algorithm(self, algorithm_name: str) -> Optional[Algorithm]:
        """Récupère une instance d'algorithme par son nom."""
        if algorithm_name not in self.algorithms:
            return None
            
        if self.algorithms[algorithm_name].instance is None:
            self.algorithms[algorithm_name].instance = \
                self.algorithms[algorithm_name].algorithm_class()
                
        return self.algorithms[algorithm_name].instance
