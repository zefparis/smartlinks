"""
Module defining the data structures for decisions and actions taken by the IA.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any

@dataclass
class Action:
    """Represents a recommended action to be taken."""
    action_type: str
    params: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    description: str = ""
    source_algorithm: str = ""


@dataclass
class DecisionContext:
    """Represents the context for a decision-making process."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    current_state: Dict[str, Any] = field(default_factory=dict)
    historical_data: Dict[str, Any] = field(default_factory=dict)
    active_alerts: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
