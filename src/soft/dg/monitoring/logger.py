"""
Système de journalisation avancé pour le DG autonome.

Fournit une interface structurée pour le logging des décisions, événements et métriques.
"""
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid

from ..models.decision import Decision, Action

class LogLevel(str, Enum):
    """Niveaux de log standardisés."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class LogEntry:
    """Entrée de log structurée."""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: LogLevel = LogLevel.INFO
    message: str = ""
    component: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entrée en dictionnaire."""
        return {
            "timestamp": self.timestamp,
            "level": self.level.value,
            "message": self.message,
            "component": self.component,
            "context": self.context,
            "trace_id": self.trace_id
        }
    
    def to_json(self) -> str:
        """Sérialise l'entrée en JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

class DGLogger:
    """Logger avancé pour le DG autonome."""
    
    def __init__(self, component: str = "dg"):
        """Initialise le logger pour un composant spécifique."""
        self.component = component
        self.logger = logging.getLogger(f"dg.{component}")
        self.metrics = {}
    
    def log(self, level: Union[LogLevel, str], message: str, **context) -> LogEntry:
        """Journalise un message avec un niveau et un contexte donnés."""
        if isinstance(level, str):
            level = LogLevel(level.lower())
            
        entry = LogEntry(
            level=level,
            message=message,
            component=self.component,
            context=context
        )
        
        # Log avec le niveau approprié
        log_method = getattr(self.logger, level.value, self.logger.info)
        log_method(message, extra={"dg_log": entry.to_dict()})
        
        return entry
    
    def debug(self, message: str, **context) -> LogEntry:
        """Journalise un message de débogage."""
        return self.log(LogLevel.DEBUG, message, **context)
    
    def info(self, message: str, **context) -> LogEntry:
        """Journalise un message d'information."""
        return self.log(LogLevel.INFO, message, **context)
    
    def warning(self, message: str, **context) -> LogEntry:
        """Journalise un avertissement."""
        return self.log(LogLevel.WARNING, message, **context)
    
    def error(self, message: str, **context) -> LogEntry:
        """Journalise une erreur."""
        return self.log(LogLevel.ERROR, message, **context)
    
    def critical(self, message: str, **context) -> LogEntry:
        """Journalise une erreur critique."""
        return self.log(LogLevel.CRITICAL, message, **context)
    
    def log_decision(self, decision: Decision) -> LogEntry:
        """Journalise une décision prise par le DG."""
        context = {
            "decision_id": decision.id,
            "actions": [action.to_dict() for action in decision.actions],
            "confidence": decision.confidence,
            "context": decision.context.dict() if hasattr(decision.context, 'dict') else {},
            "requires_approval": decision.requires_approval,
            "status": decision.status.value if hasattr(decision, 'status') else "unknown"
        }
        
        return self.info(
            f"Decision taken: {decision.id}",
            **{"decision": context}
        )
    
    def log_action(self, action: Action, status: str = "executed", **context) -> LogEntry:
        """Journalise l'exécution d'une action."""
        action_data = action.to_dict()
        action_data.update({
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return self.info(
            f"Action {status}: {action.action_type}",
            **{"action": action_data, **context}
        )
    
    def log_system_event(self, event_type: str, message: str, **metadata) -> LogEntry:
        """Journalise un événement système."""
        return self.info(
            f"System event: {event_type}",
            **{"event_type": event_type, "message": message, **metadata}
        )
    
    def metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Enregistre une métrique."""
        from . import metrics_logger
        
        if tags is None:
            tags = {}
            
        metric_data = {
            "name": name,
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "component": self.component,
            **tags
        }
        
        # Mise à jour du stockage local
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(metric_data)
        
        # Limite de l'historique
        if len(self.metrics[name]) > 1000:  # Garder les 1000 dernières valeurs
            self.metrics[name] = self.metrics[name][-1000:]
        
        # Journalisation
        metrics_logger.info(f"Metric recorded: {name}", extra={"metric": metric_data})
