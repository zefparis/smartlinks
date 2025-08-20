"""Policy-as-Code FastAPI router."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from .schemas import (
    PacValidationResult, PacPlanCreate, PacPlan, PacPlanDiff,
    ApprovalRequest, ApprovalResponse, Approval,
    RolloutConfig, PolicyRollout
)
from .loader import PacLoader, PacCLI
from .service import PacService, ApprovalService, RolloutService
from ..db import SessionLocal

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# from ..auth import get_current_user_role  # Comment out if auth module doesn't exist

router = APIRouter(prefix="/pac", tags=["Policy-as-Code"])

def get_pac_service(db: Session = Depends(get_db)) -> PacService:
    """Get PAC service instance."""
    return PacService(db)

def get_approval_service(db: Session = Depends(get_db)) -> ApprovalService:
    """Get approval service instance."""
    return ApprovalService(db)

def get_rollout_service(db: Session = Depends(get_db)) -> RolloutService:
    """Get rollout service instance."""
    return RolloutService(db)

@router.post("/validate", response_model=PacValidationResult)
async def validate_policies(
    yaml_content: str,
    pac_service: PacService = Depends(get_pac_service),
    role: str = Depends(get_current_user_role)
):
    """Validate YAML policies."""
    return await pac_service.validate_yaml(yaml_content)

@router.post("/plan", response_model=dict)
async def create_plan(
    plan_request: PacPlanCreate,
    pac_service: PacService = Depends(get_pac_service),
    role: str = Depends(get_current_user_role)
):
    """Create deployment plan."""
    if role not in ["admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    plan, diff = await pac_service.create_plan(plan_request)
    return {
        "plan": plan,
        "diff": diff
    }

@router.post("/apply", response_model=dict)
async def apply_plan(
    plan_id: str,
    pac_service: PacService = Depends(get_pac_service),
    role: str = Depends(get_current_user_role)
):
    """Apply deployment plan."""
    if role not in ["admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    success = await pac_service.apply_plan(plan_id)
    return {"success": success}

@router.get("/plans", response_model=List[PacPlan])
async def list_plans(
    author: Optional[str] = None,
    status: Optional[str] = None,
    pac_service: PacService = Depends(get_pac_service),
    role: str = Depends(get_current_user_role)
):
    """List deployment plans."""
    return await pac_service.list_plans(author=author, status=status)

@router.get("/export")
async def export_policies(
    pac_service: PacService = Depends(get_pac_service),
    role: str = Depends(get_current_user_role)
):
    """Export all policies as YAML."""
    yaml_content = await pac_service.export_policies()
    return {"yaml": yaml_content}

# Approval endpoints
@router.post("/approvals", response_model=dict)
async def create_approval(
    request: ApprovalRequest,
    approval_service: ApprovalService = Depends(get_approval_service),
    role: str = Depends(get_current_user_role)
):
    """Create approval request."""
    approval_id = await approval_service.create_approval(request)
    return {"approval_id": approval_id}

@router.post("/approvals/{approval_id}/approve")
async def approve_request(
    approval_id: str,
    response: ApprovalResponse,
    approval_service: ApprovalService = Depends(get_approval_service),
    role: str = Depends(get_current_user_role)
):
    """Approve or reject request."""
    if role not in ["admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    await approval_service.decide_approval(approval_id, response)
    return {"success": True}

@router.get("/approvals", response_model=List[Approval])
async def list_approvals(
    status: Optional[str] = None,
    algo_key: Optional[str] = None,
    approval_service: ApprovalService = Depends(get_approval_service),
    role: str = Depends(get_current_user_role)
):
    """List approval requests."""
    return await approval_service.list_approvals(status=status, algo_key=algo_key)

# Rollout endpoints
@router.post("/rollouts", response_model=dict)
async def create_rollout(
    config: RolloutConfig,
    rollout_service: RolloutService = Depends(get_rollout_service),
    role: str = Depends(get_current_user_role)
):
    """Start policy rollout."""
    if role not in ["admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    rollout_id = await rollout_service.start_rollout(config)
    return {"rollout_id": rollout_id}

@router.post("/rollouts/{rollout_id}/rollback")
async def rollback_rollout(
    rollout_id: str,
    reason: str,
    rollout_service: RolloutService = Depends(get_rollout_service),
    role: str = Depends(get_current_user_role)
):
    """Rollback policy rollout."""
    if role not in ["admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    await rollout_service.rollback_rollout(rollout_id, reason)
    return {"success": True}

@router.get("/rollouts", response_model=List[PolicyRollout])
async def list_rollouts(
    policy_id: Optional[str] = None,
    state: Optional[str] = None,
    rollout_service: RolloutService = Depends(get_rollout_service),
    role: str = Depends(get_current_user_role)
):
    """List policy rollouts."""
    return await rollout_service.list_rollouts(policy_id=policy_id, state=state)
