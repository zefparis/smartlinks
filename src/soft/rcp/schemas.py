"""
Pydantic schemas for Runtime Control Policies (RCP).
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum


# Enums
Scope = Literal["global", "algorithm", "segment"]
Mode = Literal["monitor", "enforce"]
Authority = Literal["operator", "admin", "dg_ai"]
ResultType = Literal["allowed", "modified", "blocked", "mixed"]


class GuardLimits(BaseModel):
    """Hard guard limits that cannot be exceeded."""
    weight_delta_max: Optional[float] = Field(0.20, description="Maximum weight change per action")
    budget_shift_max_percent: Optional[float] = Field(0.20, description="Maximum budget shift percentage")
    pause_dest_max_per_day: Optional[int] = Field(2, description="Maximum destinations to pause per day")
    risk_ceiling_per_tick: Optional[float] = Field(1.0, description="Maximum risk score per evaluation")
    actions_per_tick: Optional[int] = Field(50, description="Maximum actions per evaluation")


class SoftGuards(BaseModel):
    """Soft guards that trigger warnings or require approval."""
    require_explain: bool = Field(True, description="Require explanation for actions")
    require_plan_id: bool = Field(True, description="Require plan ID for actions")
    two_man_rule_threshold: Optional[float] = Field(0.15, description="Threshold for requiring approval")


class RateLimits(BaseModel):
    """Rate limiting configuration."""
    window_seconds: int = Field(3600, description="Time window in seconds")
    max_actions_in_window: int = Field(100, description="Maximum actions in time window")


class GateCondition(BaseModel):
    """Conditional gate that must be satisfied for policy to apply."""
    left: str = Field(..., description="Left side of comparison (e.g., 'metrics.cvr_1h')")
    op: Literal["<", "<=", "==", ">=", ">", "ratio_lt", "ratio_gt"] = Field(..., description="Comparison operator")
    right: Union[str, float] = Field(..., description="Right side of comparison")
    factor: Optional[float] = Field(None, description="Factor for ratio operations")

    @validator('op')
    def validate_operator(cls, v):
        valid_ops = ["<", "<=", "==", ">=", ">", "ratio_lt", "ratio_gt"]
        if v not in valid_ops:
            raise ValueError(f"Operator must be one of {valid_ops}")
        return v


class MutationRule(BaseModel):
    """Rules for mutating actions before application."""
    action_type: str = Field(..., description="Type of action to mutate")
    clamp_fields: Optional[Dict[str, Dict[str, float]]] = Field(
        None, 
        description="Fields to clamp with min/max values"
    )
    max_delta_fields: Optional[Dict[str, float]] = Field(
        None, 
        description="Maximum delta for specific fields"
    )
    block_if_missing_fields: Optional[List[str]] = Field(
        None, 
        description="Block action if these fields are missing"
    )


class Selector(BaseModel):
    """Segment selector for targeting specific traffic."""
    geo: Optional[List[str]] = Field(None, description="Geographic regions")
    device: Optional[List[str]] = Field(None, description="Device types")
    source: Optional[List[str]] = Field(None, description="Traffic sources")
    destination_ids: Optional[List[int]] = Field(None, description="Destination IDs")


class ActionDTO(BaseModel):
    """Data transfer object for algorithm actions."""
    id: str = Field(..., description="Unique action identifier")
    type: str = Field(..., description="Action type")
    algo_key: str = Field(..., description="Algorithm that generated the action")
    idempotency_key: str = Field(..., description="Idempotency key for the action")
    data: Dict[str, Any] = Field(..., description="Action-specific data")
    risk_score: Optional[float] = Field(0.0, description="Calculated risk score")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RCPPolicyCreate(BaseModel):
    """Schema for creating RCP policies."""
    id: str = Field(..., description="Unique policy identifier")
    name: str = Field(..., description="Human-readable policy name")
    scope: Scope = Field("global", description="Policy scope")
    algo_key: Optional[str] = Field(None, description="Algorithm key for algorithm-scoped policies")
    selector: Optional[Selector] = Field(None, description="Segment selector")
    mode: Mode = Field("enforce", description="Policy mode")
    authority_required: Authority = Field("dg_ai", description="Required authority level")
    hard_guards: GuardLimits = Field(default_factory=GuardLimits)
    soft_guards: SoftGuards = Field(default_factory=SoftGuards)
    limits: RateLimits = Field(default_factory=RateLimits)
    gates: List[GateCondition] = Field(default_factory=list)
    mutations: List[MutationRule] = Field(default_factory=list)
    schedule_cron: Optional[str] = Field(None, description="Cron schedule for policy activation")
    rollout_percent: float = Field(1.0, ge=0.0, le=1.0, description="Rollout percentage")
    expires_at: Optional[datetime] = Field(None, description="Policy expiration time")
    enabled: bool = Field(True, description="Whether policy is enabled")


class RCPPolicyUpdate(BaseModel):
    """Schema for updating RCP policies."""
    name: Optional[str] = None
    scope: Optional[Scope] = None
    algo_key: Optional[str] = None
    selector: Optional[Selector] = None
    mode: Optional[Mode] = None
    authority_required: Optional[Authority] = None
    hard_guards: Optional[GuardLimits] = None
    soft_guards: Optional[SoftGuards] = None
    limits: Optional[RateLimits] = None
    gates: Optional[List[GateCondition]] = None
    mutations: Optional[List[MutationRule]] = None
    schedule_cron: Optional[str] = None
    rollout_percent: Optional[float] = Field(None, ge=0.0, le=1.0)
    expires_at: Optional[datetime] = None
    enabled: Optional[bool] = None


class RCPPolicy(RCPPolicyCreate):
    """Complete RCP policy schema with metadata."""
    version: int = Field(..., description="Policy version")
    updated_by: Optional[str] = Field(None, description="Last updated by")
    updated_at: datetime = Field(..., description="Last update time")
    created_at: datetime = Field(..., description="Creation time")

    class Config:
        from_attributes = True


class RCPResult(BaseModel):
    """Result of RCP policy evaluation."""
    allowed: List[ActionDTO] = Field(default_factory=list, description="Actions allowed to proceed")
    modified: List[ActionDTO] = Field(default_factory=list, description="Actions modified before proceeding")
    blocked: List[ActionDTO] = Field(default_factory=list, description="Actions blocked")
    notes: List[str] = Field(default_factory=list, description="Evaluation notes and warnings")
    risk_cost: float = Field(0.0, description="Total risk cost of evaluation")


class RCPEvaluationStats(BaseModel):
    """Statistics from RCP evaluation."""
    risk_cost: float = Field(0.0, description="Risk cost")
    actions_allowed: int = Field(0, description="Number of actions allowed")
    actions_modified: int = Field(0, description="Number of actions modified")
    actions_blocked: int = Field(0, description="Number of actions blocked")
    evaluation_time_ms: float = Field(0.0, description="Evaluation time in milliseconds")
    policies_applied: int = Field(0, description="Number of policies applied")


class RCPEvaluationDiff(BaseModel):
    """Diff showing before/after actions."""
    before: List[ActionDTO] = Field(default_factory=list, description="Actions before evaluation")
    after: List[ActionDTO] = Field(default_factory=list, description="Actions after evaluation")
    changes: List[str] = Field(default_factory=list, description="Description of changes made")


class RCPEvaluation(BaseModel):
    """RCP evaluation record."""
    id: str = Field(..., description="Evaluation ID")
    policy_id: str = Field(..., description="Policy ID")
    algo_key: str = Field(..., description="Algorithm key")
    run_id: Optional[str] = Field(None, description="Algorithm run ID")
    result: ResultType = Field(..., description="Evaluation result")
    stats: RCPEvaluationStats = Field(..., description="Evaluation statistics")
    diff: RCPEvaluationDiff = Field(..., description="Before/after diff")
    created_at: datetime = Field(..., description="Evaluation time")

    class Config:
        from_attributes = True


class RCPPreviewRequest(BaseModel):
    """Request for RCP preview evaluation."""
    algo_key: str = Field(..., description="Algorithm key")
    ctx: Dict[str, Any] = Field(..., description="Evaluation context")
    actions: List[ActionDTO] = Field(..., description="Actions to evaluate")


class RCPEvaluationContext(BaseModel):
    """Context for RCP evaluation."""
    algo_key: str = Field(..., description="Algorithm key")
    run_id: Optional[str] = Field(None, description="Algorithm run ID")
    user_role: Optional[str] = Field(None, description="User role for RBAC")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Current metrics")
    segment_data: Dict[str, Any] = Field(default_factory=dict, description="Segment information")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    manual_override_active: bool = Field(False, description="Whether manual override is active")


class RCPPolicyList(BaseModel):
    """List of RCP policies with pagination."""
    policies: List[RCPPolicy] = Field(..., description="List of policies")
    total: int = Field(..., description="Total number of policies")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")


class RCPEvaluationList(BaseModel):
    """List of RCP evaluations with pagination."""
    evaluations: List[RCPEvaluation] = Field(..., description="List of evaluations")
    total: int = Field(..., description="Total number of evaluations")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")
