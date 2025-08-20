"""Pydantic schemas for autopilot algorithm settings and AI governance."""

from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class AuthorityLevel(str, Enum):
    """AI authority levels for algorithm governance."""
    ADVISORY = "advisory"
    SAFE_APPLY = "safe_apply"
    FULL_CONTROL = "full_control"


class CommonSettings(BaseModel):
    """Base settings common to all algorithms."""
    active: bool = True
    interval_seconds: int = Field(default=300, ge=60, le=3600)
    cooldown_seconds: int = Field(default=120, ge=30, le=600)
    dry_run: bool = False
    audit_tag: Optional[str] = None
    max_actions_per_tick: int = Field(default=50, ge=1, le=1000)
    max_risk_score_per_tick: float = Field(default=1.0, ge=0.0, le=1.0)


class TrafficOptimizerSettings(CommonSettings):
    """Traffic Optimizer algorithm settings."""
    objective: Literal["cvr", "revenue", "ctr"] = "cvr"
    exploration_ratio: float = Field(default=0.1, ge=0.0, le=0.5)
    learning_rate: float = Field(default=0.2, ge=0.01, le=1.0)
    smoothing_min_samples: int = Field(default=50, ge=10, le=1000)
    reweight_max_delta: float = Field(default=0.15, ge=0.01, le=0.5)
    weight_floor: float = Field(default=0.01, ge=0.001, le=0.1)
    weight_cap: float = Field(default=0.8, ge=0.1, le=1.0)
    min_conversions_for_action: int = Field(default=5, ge=1, le=100)
    attr_window_minutes: int = Field(default=30, ge=5, le=120)
    segmenting: Dict[str, bool] = Field(default={"geo": True, "device": True, "source": False})
    whitelist_destinations: List[int] = Field(default=[])
    blacklist_destinations: List[int] = Field(default=[])
    daily_caps: Dict[int, float] = Field(default={})
    canary_percent: float = Field(default=0.05, ge=0.0, le=0.2)
    enable_aa_experiments: bool = False


class AnomalyDetectorSettings(CommonSettings):
    """Anomaly Detector algorithm settings."""
    watched_metrics: List[str] = Field(default=["cvr", "clicks", "errors", "latency_ms"])
    sensitivity: Literal["low", "medium", "high"] = "medium"
    baseline: Literal["24h_mean", "7d_seasonal"] = "24h_mean"
    detect_window_minutes: int = Field(default=60, ge=5, le=240)
    min_volume: int = Field(default=200, ge=10, le=10000)
    hysteresis_ratio: float = Field(default=0.2, ge=0.0, le=0.5)
    alert_channels: List[str] = Field(default=["log", "email"])
    auto_mitigations: Dict[str, bool] = Field(default={
        "pause_dest_on_spike_errors": True,
        "reroute_traffic_on_cvr_drop": True
    })
    mitigation_limits: Dict[str, int] = Field(default={
        "max_pauses_per_day": 3,
        "max_reroutes_per_day": 3
    })
    slo: Dict[str, int] = Field(default={"mttd_minutes": 10, "mttr_minutes": 30})


class BudgetArbitrageSettings(CommonSettings):
    """Budget Arbitrage algorithm settings."""
    pacing: Literal["uniform", "asap", "smart"] = "smart"
    roi_constraint: Literal["none", "cpa", "cpl", "roas"] = "cpa"
    roi_target_value: float = Field(default=5.0, ge=0.1, le=1000.0)
    priority_tiers: Dict[str, List[int]] = Field(default={
        "tier1": [], "tier2": [], "tier3": []
    })
    reallocation_min_step: float = Field(default=0.05, ge=0.01, le=0.5)
    reallocation_period_minutes: int = Field(default=30, ge=5, le=240)
    overspend_guard_percent: float = Field(default=0.1, ge=0.0, le=0.5)
    carryover_unspent: bool = True
    day_reset_tz: str = "Europe/Paris"
    move_frequency_limit_per_hour: int = Field(default=6, ge=1, le=60)


class PredictiveAlertingSettings(CommonSettings):
    """Predictive Alerting algorithm settings."""
    targets: List[str] = Field(default=["traffic_spike", "conversion_drop", "error_surge"])
    horizon_minutes: int = Field(default=120, ge=15, le=720)
    confidence_threshold: float = Field(default=0.75, ge=0.5, le=0.99)
    min_lead_time_minutes: int = Field(default=15, ge=5, le=120)
    playbooks: Dict[str, List[str]] = Field(default={
        "traffic_spike": ["scale_up_router"],
        "conversion_drop": ["notify_marketing"]
    })
    quiet_hours: Dict[str, Any] = Field(default={
        "enabled": False,
        "start": "22:00",
        "end": "07:00",
        "tz": "Europe/Paris"
    })


class SelfHealingSettings(CommonSettings):
    """Self-Healing algorithm settings."""
    detectors: Dict[str, bool] = Field(default={
        "healthz": True,
        "latency": True,
        "error_rate": True
    })
    remediation: Dict[str, bool] = Field(default={
        "restart_service": True,
        "disable_probe": True,
        "rollback_route": True
    })
    retry_policy: Dict[str, Any] = Field(default={
        "max_retries": 3,
        "backoff_seconds": 60
    })
    blast_radius_cap_percent: float = Field(default=0.1, ge=0.01, le=0.5)
    escalation: Dict[str, Any] = Field(default={
        "to": ["oncall@smartlinks"],
        "after_minutes": 20
    })
    freeze_after_failures: int = Field(default=2, ge=1, le=10)


class AIPolicy(BaseModel):
    """AI governance policy for algorithms."""
    authority: AuthorityLevel = AuthorityLevel.SAFE_APPLY
    risk_budget_daily: int = Field(default=3, ge=0, le=100)
    dry_run: bool = False
    hard_guards: Dict[str, float] = Field(default={
        "weight_delta_max": 0.2,
        "budget_shift_max_percent": 0.2,
        "pause_dest_max_per_day": 2
    })
    soft_guards: Dict[str, bool] = Field(default={
        "require_explain": True,
        "require_plan_id": True
    })


# Response schemas
class AlgorithmSettingsResponse(BaseModel):
    """Response for algorithm settings with metadata."""
    settings: Dict[str, Any]
    schema: Dict[str, Any]
    version: int
    updated_by: str
    updated_at: str


class AuditEntry(BaseModel):
    """Audit log entry for settings changes."""
    id: int
    algo_key: str
    actor: str
    diff_json: Dict[str, Any]
    created_at: str


class PreviewAction(BaseModel):
    """Preview of algorithm action."""
    action_type: str
    target: str
    current_value: Any
    proposed_value: Any
    risk_score: float
    justification: str


class PreviewResponse(BaseModel):
    """Preview response for algorithm run."""
    actions: List[PreviewAction]
    total_risk_score: float
    estimated_impact: Dict[str, Any]
    warnings: List[str]


# Algorithm key to settings class mapping
ALGORITHM_SETTINGS_MAP = {
    "traffic_optimizer": TrafficOptimizerSettings,
    "anomaly_detector": AnomalyDetectorSettings,
    "budget_arbitrage": BudgetArbitrageSettings,
    "predictive_alerting": PredictiveAlertingSettings,
    "self_healing": SelfHealingSettings,
}
