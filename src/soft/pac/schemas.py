"""Policy-as-Code Pydantic schemas."""

from datetime import datetime
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, validator
from ..rcp.schemas import RCPPolicy, ActionDTO

class PacMetadata(BaseModel):
    """Metadata for Policy-as-Code resources."""
    id: str
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None

class PacPolicy(BaseModel):
    """Policy-as-Code YAML schema."""
    apiVersion: Literal["smartlinks/v1"] = "smartlinks/v1"
    kind: Literal["RCPPolicy"] = "RCPPolicy"
    metadata: PacMetadata
    spec: RCPPolicy

    @validator('metadata')
    def validate_metadata_id(cls, v):
        if not v.id:
            raise ValueError("metadata.id is required")
        return v

class PacPlan(BaseModel):
    """Policy deployment plan."""
    id: str
    author: str
    diff: Dict[str, List[str]]  # {"create": [...], "update": [...], "delete": [...]}
    dry_run: bool = True
    status: Literal["pending", "applied", "failed"] = "pending"
    created_at: datetime
    applied_at: Optional[datetime] = None
    error_message: Optional[str] = None

class PacPlanCreate(BaseModel):
    """Create a new PAC plan."""
    policies: List[PacPolicy]
    dry_run: bool = True
    author: str

class PacPlanDiff(BaseModel):
    """Policy plan diff result."""
    create: List[str] = []
    update: List[str] = []
    delete: List[str] = []
    total_changes: int = 0

    def __init__(self, **data):
        super().__init__(**data)
        self.total_changes = len(self.create) + len(self.update) + len(self.delete)

class PacValidationResult(BaseModel):
    """Policy validation result."""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    normalized: Optional[List[PacPolicy]] = None

class ApprovalRequest(BaseModel):
    """Approval request for high-risk actions."""
    algo_key: str
    actions: List[ActionDTO]
    risk_cost: float
    reason: str
    ctx_hash: str
    requested_by: str

class ApprovalResponse(BaseModel):
    """Approval decision."""
    id: str
    status: Literal["approved", "rejected"]
    decided_by: str
    note: Optional[str] = None

class Approval(BaseModel):
    """Approval record."""
    id: str
    algo_key: str
    run_id: Optional[str] = None
    reason: str
    risk_cost: float
    actions: List[ActionDTO]
    ctx_hash: str
    status: Literal["pending", "approved", "rejected"]
    requested_by: str
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    note: Optional[str] = None
    created_at: datetime

class RolloutConfig(BaseModel):
    """Policy rollout configuration."""
    policy_id: str
    to_percent: float = Field(..., ge=0.0, le=100.0)
    auto_rollback_rule: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None

class PolicyRollout(BaseModel):
    """Policy rollout record."""
    id: str
    policy_id: str
    from_percent: float
    to_percent: float
    state: Literal["pending", "active", "completed", "rolled_back"]
    reason: Optional[str] = None
    auto_rollback_rule: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class FeatureSnapshot(BaseModel):
    """Feature store snapshot."""
    id: str
    ts: datetime
    key: str
    value: Dict[str, Any]
    source: str
    tenant_id: Optional[str] = None
    created_at: datetime

class DecisionNode(BaseModel):
    """Decision graph node."""
    id: str
    type: Literal["metric", "gate", "guard", "mutation", "action", "result"]
    label: str
    value: Optional[Any] = None
    status: Optional[Literal["pass", "fail", "skip"]] = None
    metadata: Optional[Dict[str, Any]] = None

class DecisionEdge(BaseModel):
    """Decision graph edge."""
    from_node: str
    to_node: str
    label: Optional[str] = None
    condition: Optional[str] = None

class DecisionGraph(BaseModel):
    """Complete decision graph for a run."""
    run_id: str
    algo_key: str
    timestamp: datetime
    nodes: List[DecisionNode]
    edges: List[DecisionEdge]
    context: Dict[str, Any]
    final_result: Dict[str, Any]

class ReplayRequest(BaseModel):
    """Replay simulation request."""
    algo_key: str
    timestamp: datetime
    horizon_minutes: int = 60
    actions: Optional[List[ActionDTO]] = None
    context_override: Optional[Dict[str, Any]] = None

class WhatIfRequest(BaseModel):
    """What-if simulation request."""
    algo_key: str
    base_context: Dict[str, Any]
    sliders: Dict[str, float]  # {"volume_multiplier": 1.2, "cvr_adjustment": 0.05}
    seed: Optional[int] = None

class ShadowRunConfig(BaseModel):
    """Shadow run configuration."""
    algo_key: str
    enabled: bool
    duration_minutes: Optional[int] = None
    sample_rate: float = Field(1.0, ge=0.0, le=1.0)

class WebhookConfig(BaseModel):
    """Webhook configuration."""
    id: str
    name: str
    url: str
    events: List[Literal["run", "block", "alert", "approval"]]
    secret: str
    enabled: bool = True
    headers: Optional[Dict[str, str]] = None

class WebhookEvent(BaseModel):
    """Webhook event payload."""
    event_type: Literal["run", "block", "alert", "approval"]
    timestamp: datetime
    algo_key: str
    run_id: Optional[str] = None
    data: Dict[str, Any]
    signature: str
