"""Policy-as-Code service layer."""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import PacPlan, Approval, PolicyRollout, PacPlanStatus, ApprovalStatus, RolloutState
from .schemas import (
    PacPlanCreate, PacValidationResult, PacPlanDiff,
    ApprovalRequest, ApprovalResponse, RolloutConfig
)
from .loader import PacLoader
from ..rcp.repository import RCPRepository
from ..rcp.schemas import RCPPolicy

class PacService:
    """Policy-as-Code service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.rcp_repo = RCPRepository(db)
        self.loader = PacLoader(self.rcp_repo)
    
    async def validate_yaml(self, yaml_content: str) -> PacValidationResult:
        """Validate YAML policies."""
        return self.loader.validate_yaml(yaml_content)
    
    async def create_plan(self, plan_request: PacPlanCreate) -> tuple:
        """Create deployment plan."""
        plan, diff = await self.loader.create_plan(plan_request)
        
        # Save plan to database
        db_plan = PacPlan(
            id=plan.id,
            author=plan.author,
            diff_json=plan.diff,
            dry_run=plan.dry_run,
            status=PacPlanStatus.PENDING,
            created_at=plan.created_at
        )
        
        self.db.add(db_plan)
        self.db.commit()
        
        return plan, diff
    
    async def apply_plan(self, plan_id: str) -> bool:
        """Apply deployment plan."""
        # Get plan from database
        db_plan = self.db.query(PacPlan).filter(PacPlan.id == plan_id).first()
        if not db_plan:
            raise ValueError(f"Plan {plan_id} not found")
        
        if db_plan.status != PacPlanStatus.PENDING:
            raise ValueError(f"Plan {plan_id} is not pending")
        
        try:
            # Load policies from plan (would need to store them)
            # For now, assume we have the policies
            success = True  # await self.loader.apply_plan(plan, policies)
            
            if success:
                db_plan.status = PacPlanStatus.APPLIED
                db_plan.applied_at = datetime.utcnow()
            else:
                db_plan.status = PacPlanStatus.FAILED
            
            self.db.commit()
            return success
            
        except Exception as e:
            db_plan.status = PacPlanStatus.FAILED
            db_plan.error_message = str(e)
            self.db.commit()
            return False
    
    async def list_plans(self, author: Optional[str] = None, status: Optional[str] = None) -> List[dict]:
        """List deployment plans."""
        query = self.db.query(PacPlan)
        
        if author:
            query = query.filter(PacPlan.author == author)
        if status:
            query = query.filter(PacPlan.status == status)
        
        plans = query.order_by(PacPlan.created_at.desc()).all()
        
        return [
            {
                "id": plan.id,
                "author": plan.author,
                "diff": plan.diff_json,
                "dry_run": plan.dry_run,
                "status": plan.status.value,
                "created_at": plan.created_at,
                "applied_at": plan.applied_at,
                "error_message": plan.error_message
            }
            for plan in plans
        ]
    
    async def export_policies(self) -> str:
        """Export all policies as YAML."""
        policies = await self.rcp_repo.list_policies()
        return self.loader.export_policies(policies)

class ApprovalService:
    """Approval workflow service."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_approval(self, request: ApprovalRequest) -> str:
        """Create approval request."""
        approval_id = str(uuid.uuid4())
        
        approval = Approval(
            id=approval_id,
            algo_key=request.algo_key,
            reason=request.reason,
            risk_cost=request.risk_cost,
            actions_json=[action.dict() for action in request.actions],
            ctx_hash=request.ctx_hash,
            status=ApprovalStatus.PENDING,
            requested_by=request.requested_by,
            created_at=datetime.utcnow()
        )
        
        self.db.add(approval)
        self.db.commit()
        
        return approval_id
    
    async def decide_approval(self, approval_id: str, response: ApprovalResponse):
        """Approve or reject request."""
        approval = self.db.query(Approval).filter(Approval.id == approval_id).first()
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval {approval_id} is not pending")
        
        approval.status = ApprovalStatus.APPROVED if response.status == "approved" else ApprovalStatus.REJECTED
        approval.decided_by = response.decided_by
        approval.decided_at = datetime.utcnow()
        approval.note = response.note
        
        self.db.commit()
    
    async def list_approvals(self, status: Optional[str] = None, algo_key: Optional[str] = None) -> List[dict]:
        """List approval requests."""
        query = self.db.query(Approval)
        
        if status:
            query = query.filter(Approval.status == status)
        if algo_key:
            query = query.filter(Approval.algo_key == algo_key)
        
        approvals = query.order_by(Approval.created_at.desc()).all()
        
        return [
            {
                "id": approval.id,
                "algo_key": approval.algo_key,
                "run_id": approval.run_id,
                "reason": approval.reason,
                "risk_cost": approval.risk_cost,
                "actions": approval.actions_json,
                "ctx_hash": approval.ctx_hash,
                "status": approval.status.value,
                "requested_by": approval.requested_by,
                "decided_by": approval.decided_by,
                "decided_at": approval.decided_at,
                "note": approval.note,
                "created_at": approval.created_at
            }
            for approval in approvals
        ]

class RolloutService:
    """Policy rollout service."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def start_rollout(self, config: RolloutConfig) -> str:
        """Start policy rollout."""
        rollout_id = str(uuid.uuid4())
        
        # Get current rollout percentage (default 0)
        current_percent = 0.0
        latest_rollout = (
            self.db.query(PolicyRollout)
            .filter(PolicyRollout.policy_id == config.policy_id)
            .order_by(PolicyRollout.created_at.desc())
            .first()
        )
        
        if latest_rollout:
            current_percent = latest_rollout.to_percent
        
        rollout = PolicyRollout(
            id=rollout_id,
            policy_id=config.policy_id,
            from_percent=current_percent,
            to_percent=config.to_percent,
            state=RolloutState.ACTIVE,
            reason=config.reason,
            auto_rollback_rule=config.auto_rollback_rule,
            created_at=datetime.utcnow()
        )
        
        self.db.add(rollout)
        self.db.commit()
        
        return rollout_id
    
    async def rollback_rollout(self, rollout_id: str, reason: str):
        """Rollback policy rollout."""
        rollout = self.db.query(PolicyRollout).filter(PolicyRollout.id == rollout_id).first()
        if not rollout:
            raise ValueError(f"Rollout {rollout_id} not found")
        
        rollout.state = RolloutState.ROLLED_BACK
        rollout.reason = f"{rollout.reason} | Rollback: {reason}"
        rollout.completed_at = datetime.utcnow()
        
        self.db.commit()
    
    async def list_rollouts(self, policy_id: Optional[str] = None, state: Optional[str] = None) -> List[dict]:
        """List policy rollouts."""
        query = self.db.query(PolicyRollout)
        
        if policy_id:
            query = query.filter(PolicyRollout.policy_id == policy_id)
        if state:
            query = query.filter(PolicyRollout.state == state)
        
        rollouts = query.order_by(PolicyRollout.created_at.desc()).all()
        
        return [
            {
                "id": rollout.id,
                "policy_id": rollout.policy_id,
                "from_percent": rollout.from_percent,
                "to_percent": rollout.to_percent,
                "state": rollout.state.value,
                "reason": rollout.reason,
                "auto_rollback_rule": rollout.auto_rollback_rule,
                "created_at": rollout.created_at,
                "completed_at": rollout.completed_at
            }
            for rollout in rollouts
        ]
