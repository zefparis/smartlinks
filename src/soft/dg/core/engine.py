"""
Moteur principal du DG autonome.

Gère le cycle de vie du système, l'orchestration des algorithmes
et la prise de décision en temps réel.
"""
from typing import Dict, Any, List, Optional
import logging
from enum import Enum, auto
from datetime import datetime

from ..monitoring.logger import DGLogger
from ..models.decision import Decision, DecisionContext, Action
from .strategy import StrategyEngine
from .state import SystemState

logger = logging.getLogger(__name__)

class DGMode(Enum):
    """Modes de fonctionnement du DG autonome."""
    AUTO = auto()      # Mode entièrement autonome
    SEMI_AUTO = auto() # Mode semi-autonome (validation humaine requise)
    MANUAL = auto()    # Mode manuel (aucune action automatique)
    MAINTENANCE = auto() # Mode maintenance (actions limitées)

class DGEngine:
    """Moteur principal du DG autonome."""
    
    def __init__(self, db_session_factory=None):
        """Initialise le moteur DG.
        
        Args:
            db_session_factory: Fabrique de sessions SQLAlchemy
        """
        self.mode = DGMode.MANUAL
        self.strategy_engine = StrategyEngine()
        self.state = SystemState()
        self.logger = DGLogger()
        self.db_session_factory = db_session_factory
        self._last_decision = None
        self._metrics = {}
        
    def set_mode(self, mode: DGMode) -> bool:
        """Change le mode de fonctionnement du DG.
        
        Args:
            mode: Nouveau mode (AUTO, SEMI_AUTO, MANUAL, MAINTENANCE)
            
        Returns:
            bool: True si le changement a réussi
        """
        old_mode = self.mode
        self.mode = mode
        self.logger.log_system_event(
            "mode_change",
            f"Changement de mode: {old_mode.name} → {mode.name}",
            metadata={"old_mode": old_mode.name, "new_mode": mode.name}
        )
        return True
    
    async def analyze(self, context: Dict[str, Any]) -> DecisionContext:
        """Analyse le contexte actuel et prépare une décision.
        
        Args:
            context: Contexte d'analyse (métriques, logs, etc.)
            
        Returns:
            DecisionContext: Contexte de décision préparé
        """
        # Mise à jour de l'état interne
        self.state.update(context)
        
        # Préparation du contexte de décision
        decision_context = DecisionContext(
            timestamp=datetime.utcnow(),
            system_state=self.state.current_state,
            metrics=context.get('metrics', {}),
            events=context.get('events', []),
            mode=self.mode
        )
        
        # Analyse par le moteur de stratégie
        decision_context = await self.strategy_engine.analyze(decision_context)
        
        return decision_context
    
    async def decide(self, context: Dict[str, Any]) -> Optional[Decision]:
        """Prend une décision basée sur l'analyse du contexte.
        
        Args:
            context: Contexte d'analyse
            
        Returns:
            Decision: Décision prise, ou None si aucune décision
        """
        if self.mode == DGMode.MANUAL:
            return None
            
        # Analyse du contexte
        decision_context = await self.analyze(context)
        
        # Décision
        decision = Decision(
            timestamp=datetime.utcnow(),
            context=decision_context,
            actions=[],
            confidence=0.0,
            requires_approval=self.mode == DGMode.SEMI_AUTO
        )
        
        # Sélection des actions recommandées
        if decision_context.recommended_actions:
            decision.actions = decision_context.recommended_actions
            decision.confidence = decision_context.confidence
            
            # Enregistrement de la décision
            self._last_decision = decision
            self.log_decision(decision)
            
            # Exécution automatique si en mode AUTO
            if self.mode == DGMode.AUTO and not decision.requires_approval:
                await self.execute_decision(decision)
        
        return decision if decision.actions else None
    
    async def execute_decision(self, decision: Decision) -> Dict[str, Any]:
        """Exécute une décision précédemment prise.
        
        Args:
            decision: Décision à exécuter
            
        Returns:
            Dict: Résultats de l'exécution
        """
        results = {
            "executed_actions": [],
            "failed_actions": [],
            "start_time": datetime.utcnow()
        }
        
        # Vérification des prérequis
        if self.mode not in [DGMode.AUTO, DGMode.SEMI_AUTO]:
            raise RuntimeError("Le mode actuel ne permet pas l'exécution automatique")
            
        # Exécution des actions
        for action in decision.actions:
            try:
                result = await self._execute_action(action)
                results["executed_actions"].append({
                    "action_id": action.id,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                logger.error(f"Erreur lors de l'exécution de l'action {action.id}: {e}")
                results["failed_actions"].append({
                    "action_id": action.id,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Mise à jour des métriques
        results["end_time"] = datetime.utcnow()
        results["duration"] = (results["end_time"] - results["start_time"].total_seconds())
        
        # Journalisation
        self.logger.log_system_event(
            "decision_executed",
            f"Exécution de la décision: {len(results['executed_actions'])} actions exécutées, "
            f"{len(results['failed_actions'])} échecs",
            metadata=results
        )
        
        return results
    
    async def _execute_action(self, action: Action) -> Any:
        """Exécute une action spécifique.
        
        Args:
            action: Action à exécuter
            
        Returns:
            Résultat de l'exécution
            
        Raises:
            Exception: En cas d'échec de l'exécution
        """
        # Cette méthode délègue l'exécution au bon gestionnaire d'action
        # en fonction du type d'action
        handler = getattr(self, f"_handle_{action.action_type}", None)
        if not handler:
            raise ValueError(f"Type d'action non supporté: {action.action_type}")
            
        return await handler(action)
    
    def log_decision(self, decision: Decision):
        """Journalise une décision."""
        self.logger.log_decision(decision)
        
    def get_status(self) -> Dict[str, Any]:
        """Retourne l'état actuel du moteur."""
        return {
            "mode": self.mode.name,
            "last_decision": self._last_decision.to_dict() if self._last_decision else None,
            "metrics": self._metrics,
            "state": self.state.current_state
        }
    
    # Méthodes de gestion d'actions spécifiques
    
    async def _handle_algorithm_activation(self, action: Action) -> Dict:
        """Active ou désactive un algorithme."""
        algorithm_name = action.params["algorithm"]
        enable = action.params.get("enable", True)
        
        if enable:
            await self.strategy_engine.activate_algorithm(algorithm_name)
            return {"status": "activated", "algorithm": algorithm_name}
        else:
            await self.strategy_engine.deactivate_algorithm(algorithm_name)
            return {"status": "deactivated", "algorithm": algorithm_name}
    
    async def _handle_config_update(self, action: Action) -> Dict:
        """Met à jour la configuration du système."""
        config_key = action.params["key"]
        value = action.params["value"]
        
        # Ici, on pourrait implémenter la logique de mise à jour
        # de la configuration système
        
        return {
            "status": "updated",
            "config_key": config_key,
            "new_value": value
        }
