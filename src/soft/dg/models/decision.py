"""
Modèles de décision pour le DG autonome.

Définit les structures de données utilisées pour la prise de décision
et l'exécution d'actions.
"""
from enum import Enum, auto
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import uuid4

class ActionStatus(str, Enum):
    """Statut d'une action."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class DecisionStatus(str, Enum):
    """Statut d'une décision."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DecisionType(str, Enum):
    """Type de décision."""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SYSTEM = "system"
    ALGORITHMIC = "algorithmic"

class Action(BaseModel):
    """Représente une action à exécuter par le système."""
    id: str = Field(default_factory=lambda: f"act_{uuid4().hex[:8]}")
    action_type: str = Field(..., description="Type d'action à exécuter")
    params: Dict[str, Any] = Field(default_factory=dict, description="Paramètres de l'action")
    priority: int = Field(default=0, description="Priorité (plus élevé = plus important)")
    status: ActionStatus = Field(default=ActionStatus.PENDING, description="Statut actuel de l'action")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Date de création")
    updated_at: Optional[datetime] = Field(default=None, description="Dernière mise à jour")
    description: str = Field(default="", description="Description lisible par un humain")
    source_algorithm: Optional[str] = Field(default=None, description="Algorithme ayant généré cette action")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées supplémentaires")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'action en dictionnaire."""
        return self.dict()
    
    def mark_as(self, status: ActionStatus, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Met à jour le statut de l'action."""
        self.status = status
        self.updated_at = datetime.utcnow()
        if metadata:
            self.metadata.update(metadata)

class DecisionContext(BaseModel):
    """Contexte d'une décision."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    system_state: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    mode: str = "auto"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    recommended_actions: List[Action] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Decision(BaseModel):
    """Représente une décision prise par le DG autonome."""
    id: str = Field(default_factory=lambda: f"dec_{uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: DecisionContext = Field(default_factory=DecisionContext)
    actions: List[Action] = Field(default_factory=list)
    status: DecisionStatus = Field(default=DecisionStatus.PENDING)
    decision_type: DecisionType = Field(default=DecisionType.ALGORITHMIC)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    requires_approval: bool = Field(default=False)
    approved_by: Optional[str] = Field(default=None)
    approved_at: Optional[datetime] = Field(default=None)
    executed_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la décision en dictionnaire."""
        return self.dict()
    
    def add_action(self, action: Action) -> None:
        """Ajoute une action à la décision."""
        self.actions.append(action)
    
    def approve(self, approved_by: str) -> None:
        """Approuve la décision."""
        self.status = DecisionStatus.APPROVED
        self.approved_by = approved_by
        self.approved_at = datetime.utcnow()
    
    def reject(self, reason: str = "") -> None:
        """Rejette la décision."""
        self.status = DecisionStatus.REJECTED
        self.metadata["rejection_reason"] = reason
    
    def mark_as_executing(self) -> None:
        """Marque la décision comme en cours d'exécution."""
        self.status = DecisionStatus.EXECUTING
        self.executed_at = datetime.utcnow()
    
    def mark_as_completed(self, results: Optional[Dict[str, Any]] = None) -> None:
        """Marque la décision comme terminée."""
        self.status = DecisionStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if results:
            self.metadata["execution_results"] = results
    
    def mark_as_failed(self, error: Optional[Exception] = None) -> None:
        """Marque la décision comme ayant échoué."""
        self.status = DecisionStatus.FAILED
        self.completed_at = datetime.utcnow()
        if error:
            self.metadata["error"] = str(error)
            self.metadata["error_type"] = error.__class__.__name__
    
    def get_action(self, action_id: str) -> Optional[Action]:
        """Récupère une action par son ID."""
        for action in self.actions:
            if action.id == action_id:
                return action
        return None
    
    def update_action_status(self, action_id: str, status: ActionStatus, 
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Met à jour le statut d'une action."""
        action = self.get_action(action_id)
        if not action:
            return False
        
        action.mark_as(status, metadata)
        return True
