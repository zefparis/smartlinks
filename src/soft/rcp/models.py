"""
SQLAlchemy models for Runtime Control Policies (RCP).
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, ForeignKey, Enum, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class RCPScope(str, enum.Enum):
    GLOBAL = "global"
    ALGORITHM = "algorithm"
    SEGMENT = "segment"


class RCPMode(str, enum.Enum):
    MONITOR = "monitor"
    ENFORCE = "enforce"


class RCPAuthority(str, enum.Enum):
    OPERATOR = "operator"
    ADMIN = "admin"
    DG_AI = "dg_ai"


class RCPResult(str, enum.Enum):
    ALLOWED = "allowed"
    MODIFIED = "modified"
    BLOCKED = "blocked"
    MIXED = "mixed"


class RCPPolicy(Base):
    """
    Runtime Control Policy model.
    
    Defines governance rules that filter, bound, and rewrite algorithm actions
    before application.
    """
    __tablename__ = "rcp_policies"

    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    scope = Column(Enum(RCPScope), nullable=False, default=RCPScope.GLOBAL)
    algo_key = Column(String(100), nullable=True)
    selector_json = Column(JSONB, nullable=True)  # Segment selectors
    mode = Column(Enum(RCPMode), nullable=False, default=RCPMode.ENFORCE)
    authority_required = Column(Enum(RCPAuthority), nullable=False, default=RCPAuthority.DG_AI)
    
    # Policy rules stored as JSON
    hard_guards_json = Column(JSONB, nullable=True)
    soft_guards_json = Column(JSONB, nullable=True)
    limits_json = Column(JSONB, nullable=True)
    gates_json = Column(JSONB, nullable=True)
    mutations_json = Column(JSONB, nullable=True)
    
    # Scheduling and rollout
    schedule_cron = Column(String(100), nullable=True)
    rollout_percent = Column(Float, nullable=False, default=1.0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    enabled = Column(Boolean, nullable=False, default=True)
    version = Column(Integer, nullable=False, default=1)
    updated_by = Column(String(100), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    evaluations = relationship("RCPEvaluation", back_populates="policy", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RCPPolicy(id='{self.id}', name='{self.name}', scope='{self.scope}')>"


class RCPEvaluation(Base):
    """
    Record of RCP policy evaluation against algorithm actions.
    
    Provides audit trail and statistics for governance decisions.
    """
    __tablename__ = "rcp_evaluations"

    id = Column(String(36), primary_key=True)
    policy_id = Column(String(255), ForeignKey("rcp_policies.id", ondelete="CASCADE"), nullable=False)
    algo_key = Column(String(100), nullable=False)
    run_id = Column(String(36), nullable=True)  # FK to algorithm_runs when available
    result = Column(Enum(RCPResult), nullable=False)
    
    # Evaluation data stored as JSON
    stats_json = Column(JSONB, nullable=True)  # risk_cost, counts, timings
    diff_json = Column(JSONB, nullable=True)   # actions before/after
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    policy = relationship("RCPPolicy", back_populates="evaluations")

    def __repr__(self):
        return f"<RCPEvaluation(id='{self.id}', policy_id='{self.policy_id}', result='{self.result}')>"
