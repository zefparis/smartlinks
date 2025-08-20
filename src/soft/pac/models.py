"""Policy-as-Code and Governance SQLAlchemy models."""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Float, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship

from ..db import Base

class PacPlanStatus(str, Enum):
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class RolloutState(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"

class PacPlan(Base):
    """Policy-as-Code deployment plan."""
    __tablename__ = "pac_plans"

    id = Column(String, primary_key=True)
    author = Column(String, nullable=False, index=True)
    diff_json = Column(JSON, nullable=False)
    dry_run = Column(Boolean, nullable=False, default=True)
    status = Column(ENUM(PacPlanStatus), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    applied_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

class Approval(Base):
    """Approval requests for high-risk actions."""
    __tablename__ = "approvals"

    id = Column(String, primary_key=True)
    algo_key = Column(String, nullable=False, index=True)
    run_id = Column(String, nullable=True)
    reason = Column(Text, nullable=False)
    risk_cost = Column(Float, nullable=False)
    actions_json = Column(JSON, nullable=False)
    ctx_hash = Column(String, nullable=False)
    status = Column(ENUM(ApprovalStatus), nullable=False, index=True)
    requested_by = Column(String, nullable=False)
    decided_by = Column(String, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

class FeatureSnapshot(Base):
    """Feature store snapshots for backtesting and replay."""
    __tablename__ = "feature_snapshots"

    id = Column(String, primary_key=True)
    ts = Column(DateTime, nullable=False, index=True)
    key = Column(String, nullable=False, index=True)
    value_json = Column(JSON, nullable=False)
    source = Column(String, nullable=False)
    tenant_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class PolicyRollout(Base):
    """Policy rollout tracking for canary deployments."""
    __tablename__ = "policy_rollouts"

    id = Column(String, primary_key=True)
    policy_id = Column(String, ForeignKey("rcp_policies.id"), nullable=False, index=True)
    from_percent = Column(Float, nullable=False)
    to_percent = Column(Float, nullable=False)
    state = Column(ENUM(RolloutState), nullable=False, index=True)
    reason = Column(Text, nullable=True)
    auto_rollback_rule = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationship to RCP policy
    policy = relationship("RCPPolicy", back_populates="rollouts")
