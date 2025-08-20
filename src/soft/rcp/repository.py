"""
Repository layer for RCP data access.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from .models import RCPPolicy, RCPEvaluation
from .schemas import (
    RCPPolicyCreate, RCPPolicyUpdate, RCPPolicy as RCPPolicySchema,
    RCPEvaluation as RCPEvaluationSchema, RCPEvaluationStats, RCPEvaluationDiff
)


class RCPRepository:
    """Repository for RCP data operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Policy CRUD operations
    
    def create_policy(self, policy_data: RCPPolicyCreate, updated_by: str = None) -> RCPPolicy:
        """Create a new RCP policy."""
        db_policy = RCPPolicy(
            id=policy_data.id,
            name=policy_data.name,
            scope=policy_data.scope,
            algo_key=policy_data.algo_key,
            selector_json=policy_data.selector.dict() if policy_data.selector else None,
            mode=policy_data.mode,
            authority_required=policy_data.authority_required,
            hard_guards_json=policy_data.hard_guards.dict(),
            soft_guards_json=policy_data.soft_guards.dict(),
            limits_json=policy_data.limits.dict(),
            gates_json=[gate.dict() for gate in policy_data.gates],
            mutations_json=[mutation.dict() for mutation in policy_data.mutations],
            schedule_cron=policy_data.schedule_cron,
            rollout_percent=policy_data.rollout_percent,
            expires_at=policy_data.expires_at,
            enabled=policy_data.enabled,
            updated_by=updated_by
        )
        
        self.db.add(db_policy)
        self.db.commit()
        self.db.refresh(db_policy)
        return db_policy
    
    def get_policy(self, policy_id: str) -> Optional[RCPPolicy]:
        """Get policy by ID."""
        return self.db.query(RCPPolicy).filter(RCPPolicy.id == policy_id).first()
    
    def list_policies(
        self, 
        scope: Optional[str] = None,
        algo_key: Optional[str] = None,
        enabled: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[RCPPolicy]:
        """List policies with optional filtering."""
        query = self.db.query(RCPPolicy)
        
        if scope:
            query = query.filter(RCPPolicy.scope == scope)
        if algo_key:
            query = query.filter(RCPPolicy.algo_key == algo_key)
        if enabled is not None:
            query = query.filter(RCPPolicy.enabled == enabled)
        
        return query.offset(skip).limit(limit).all()
    
    def update_policy(self, policy_id: str, policy_data: RCPPolicyUpdate, updated_by: str = None) -> Optional[RCPPolicy]:
        """Update an existing policy."""
        db_policy = self.get_policy(policy_id)
        if not db_policy:
            return None
        
        update_data = policy_data.dict(exclude_unset=True)
        
        # Handle nested objects
        if "selector" in update_data and update_data["selector"]:
            update_data["selector_json"] = update_data.pop("selector").dict()
        if "hard_guards" in update_data:
            update_data["hard_guards_json"] = update_data.pop("hard_guards").dict()
        if "soft_guards" in update_data:
            update_data["soft_guards_json"] = update_data.pop("soft_guards").dict()
        if "limits" in update_data:
            update_data["limits_json"] = update_data.pop("limits").dict()
        if "gates" in update_data:
            update_data["gates_json"] = [gate.dict() for gate in update_data.pop("gates")]
        if "mutations" in update_data:
            update_data["mutations_json"] = [mutation.dict() for mutation in update_data.pop("mutations")]
        
        # Update version and metadata
        update_data["version"] = db_policy.version + 1
        update_data["updated_by"] = updated_by
        update_data["updated_at"] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_policy, field, value)
        
        self.db.commit()
        self.db.refresh(db_policy)
        return db_policy
    
    def delete_policy(self, policy_id: str) -> bool:
        """Delete a policy."""
        db_policy = self.get_policy(policy_id)
        if not db_policy:
            return False
        
        self.db.delete(db_policy)
        self.db.commit()
        return True
    
    def get_applicable_policies(
        self, 
        algo_key: str, 
        enabled_only: bool = True,
        include_global: bool = True
    ) -> List[RCPPolicy]:
        """Get policies applicable to a specific algorithm."""
        conditions = []
        
        if enabled_only:
            conditions.append(RCPPolicy.enabled == True)
        
        # Algorithm-specific policies
        algo_condition = and_(
            RCPPolicy.scope == "algorithm",
            RCPPolicy.algo_key == algo_key
        )
        
        scope_conditions = [algo_condition]
        
        # Global policies
        if include_global:
            scope_conditions.append(RCPPolicy.scope == "global")
        
        # Segment policies (always included as they're filtered by evaluator)
        scope_conditions.append(RCPPolicy.scope == "segment")
        
        conditions.append(or_(*scope_conditions))
        
        # Filter out expired policies
        now = datetime.utcnow()
        conditions.append(
            or_(
                RCPPolicy.expires_at.is_(None),
                RCPPolicy.expires_at > now
            )
        )
        
        return self.db.query(RCPPolicy).filter(and_(*conditions)).all()
    
    # Evaluation operations
    
    def create_evaluation(
        self,
        policy_id: str,
        algo_key: str,
        run_id: Optional[str],
        result: str,
        stats: RCPEvaluationStats,
        diff: RCPEvaluationDiff
    ) -> RCPEvaluation:
        """Create a new evaluation record."""
        db_evaluation = RCPEvaluation(
            id=str(uuid.uuid4()),
            policy_id=policy_id,
            algo_key=algo_key,
            run_id=run_id,
            result=result,
            stats_json=stats.dict(),
            diff_json=diff.dict()
        )
        
        self.db.add(db_evaluation)
        self.db.commit()
        self.db.refresh(db_evaluation)
        return db_evaluation
    
    def list_evaluations(
        self,
        policy_id: Optional[str] = None,
        algo_key: Optional[str] = None,
        since: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[RCPEvaluation]:
        """List evaluations with optional filtering."""
        query = self.db.query(RCPEvaluation)
        
        if policy_id:
            query = query.filter(RCPEvaluation.policy_id == policy_id)
        if algo_key:
            query = query.filter(RCPEvaluation.algo_key == algo_key)
        if since:
            query = query.filter(RCPEvaluation.created_at >= since)
        
        return query.order_by(desc(RCPEvaluation.created_at)).offset(skip).limit(limit).all()
    
    def get_evaluation_stats(
        self,
        algo_key: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get aggregated evaluation statistics."""
        query = self.db.query(RCPEvaluation)
        
        if algo_key:
            query = query.filter(RCPEvaluation.algo_key == algo_key)
        if since:
            query = query.filter(RCPEvaluation.created_at >= since)
        
        evaluations = query.all()
        
        if not evaluations:
            return {
                "total_evaluations": 0,
                "results": {},
                "avg_risk_cost": 0.0,
                "total_actions": {"allowed": 0, "modified": 0, "blocked": 0}
            }
        
        results = {}
        total_risk_cost = 0.0
        total_actions = {"allowed": 0, "modified": 0, "blocked": 0}
        
        for eval in evaluations:
            # Count results
            result = eval.result
            results[result] = results.get(result, 0) + 1
            
            # Sum risk costs and action counts
            if eval.stats_json:
                stats = eval.stats_json
                total_risk_cost += stats.get("risk_cost", 0.0)
                total_actions["allowed"] += stats.get("actions_allowed", 0)
                total_actions["modified"] += stats.get("actions_modified", 0)
                total_actions["blocked"] += stats.get("actions_blocked", 0)
        
        return {
            "total_evaluations": len(evaluations),
            "results": results,
            "avg_risk_cost": total_risk_cost / len(evaluations),
            "total_actions": total_actions
        }
