"""SQLAlchemy models for autopilot algorithm settings and AI governance."""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Enum, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class AuthorityLevel(PyEnum):
    """AI authority levels for algorithm governance."""
    ADVISORY = "advisory"
    SAFE_APPLY = "safe_apply"
    FULL_CONTROL = "full_control"


class AlgorithmSettings(Base):
    """Algorithm configuration settings with versioning."""
    __tablename__ = "algorithm_settings"
    
    id = Column(Integer, primary_key=True)
    algo_key = Column(String(50), nullable=False)
    settings_json = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    updated_by = Column(String(100), nullable=False)
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('algo_key', name='uq_algorithm_settings_algo_key'),
        Index('ix_algorithm_settings_algo_key', 'algo_key'),
    )


class AIPolicy(Base):
    """AI governance policies per algorithm or global."""
    __tablename__ = "ai_policies"
    
    id = Column(Integer, primary_key=True)
    algo_key = Column(String(50), nullable=False)  # "global" for global policy
    authority = Column(Enum(AuthorityLevel), nullable=False, default=AuthorityLevel.SAFE_APPLY)
    risk_budget_daily = Column(Integer, nullable=False, default=3)
    dry_run = Column(Boolean, nullable=False, default=False)
    hard_guards_json = Column(JSON, nullable=False)
    soft_guards_json = Column(JSON, nullable=False)
    updated_by = Column(String(100), nullable=False)
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('algo_key', name='uq_ai_policies_algo_key'),
        Index('ix_ai_policies_algo_key', 'algo_key'),
    )


class AuditSettings(Base):
    """Audit log for algorithm settings changes."""
    __tablename__ = "audit_settings"
    
    id = Column(Integer, primary_key=True)
    algo_key = Column(String(50), nullable=False)
    actor = Column(String(100), nullable=False)
    diff_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('ix_audit_settings_algo_key', 'algo_key'),
        Index('ix_audit_settings_created_at', 'created_at'),
    )
