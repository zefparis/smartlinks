"""
FastAPI router for Runtime Control Policies (RCP).
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session

from ..dg.dependencies import get_db
from .repository import RCPRepository
from .evaluator import RCPEvaluator
from .schemas import (
    RCPPolicy, RCPPolicyCreate, RCPPolicyUpdate, RCPPolicyList,
    RCPEvaluation, RCPEvaluationList, RCPPreviewRequest, RCPResult,
    RCPEvaluationContext, ActionDTO
)

router = APIRouter(prefix="/rcp", tags=["Runtime Control Policies"])


def get_user_role(x_role: Optional[str] = Header(None)) -> str:
    """Extract user role from header for RBAC."""
    return x_role or "viewer"


def check_rcp_permissions(role: str, operation: str = "read") -> bool:
    """Check if user has permissions for RCP operations."""
    role_permissions = {
        "viewer": ["read"],
        "operator": ["read"],
        "admin": ["read", "write"],
        "dg_ai": ["read", "write"]
    }
    
    return operation in role_permissions.get(role, [])


@router.get("/policies", response_model=RCPPolicyList)
async def list_policies(
    scope: Optional[str] = Query(None, description="Filter by scope"),
    algo_key: Optional[str] = Query(None, description="Filter by algorithm"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    role: str = Depends(get_user_role)
):
    """List RCP policies with optional filtering."""
    if not check_rcp_permissions(role, "read"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    repo = RCPRepository(db)
    skip = (page - 1) * per_page
    
    policies = repo.list_policies(
        scope=scope,
        algo_key=algo_key,
        enabled=enabled,
        skip=skip,
        limit=per_page
    )
    
    # Count total for pagination
    total_policies = repo.list_policies(scope=scope, algo_key=algo_key, enabled=enabled)
    
    return RCPPolicyList(
        policies=[RCPPolicy.from_orm(p) for p in policies],
        total=len(total_policies),
        page=page,
        per_page=per_page
    )


@router.post("/policies", response_model=RCPPolicy)
async def create_policy(
    policy: RCPPolicyCreate,
    db: Session = Depends(get_db),
    role: str = Depends(get_user_role)
):
    """Create a new RCP policy."""
    if not check_rcp_permissions(role, "write"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    repo = RCPRepository(db)
    
    # Check if policy already exists
    existing = repo.get_policy(policy.id)
    if existing:
        raise HTTPException(status_code=409, detail="Policy already exists")
    
    try:
        db_policy = repo.create_policy(policy, updated_by=role)
        return RCPPolicy.from_orm(db_policy)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create policy: {str(e)}")


@router.get("/policies/{policy_id}", response_model=RCPPolicy)
async def get_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    role: str = Depends(get_user_role)
):
    """Get a specific RCP policy."""
    if not check_rcp_permissions(role, "read"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    repo = RCPRepository(db)
    policy = repo.get_policy(policy_id)
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return RCPPolicy.from_orm(policy)


@router.put("/policies/{policy_id}", response_model=RCPPolicy)
async def update_policy(
    policy_id: str,
    policy_update: RCPPolicyUpdate,
    db: Session = Depends(get_db),
    role: str = Depends(get_user_role)
):
    """Update an existing RCP policy."""
    if not check_rcp_permissions(role, "write"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    repo = RCPRepository(db)
    
    try:
        updated_policy = repo.update_policy(policy_id, policy_update, updated_by=role)
        if not updated_policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        return RCPPolicy.from_orm(updated_policy)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update policy: {str(e)}")


@router.delete("/policies/{policy_id}")
async def delete_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    role: str = Depends(get_user_role)
):
    """Delete an RCP policy."""
    if not check_rcp_permissions(role, "write"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    repo = RCPRepository(db)
    
    if not repo.delete_policy(policy_id):
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return {"message": "Policy deleted successfully"}


@router.post("/preview", response_model=RCPResult)
async def preview_rcp_evaluation(
    request: RCPPreviewRequest,
    db: Session = Depends(get_db),
    role: str = Depends(get_user_role)
):
    """Preview RCP evaluation without persisting results."""
    if not check_rcp_permissions(role, "read"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    repo = RCPRepository(db)
    evaluator = RCPEvaluator()
    
    try:
        # Get applicable policies
        policies = repo.get_applicable_policies(request.algo_key)
        
        # Convert to Pydantic models
        policy_schemas = [RCPPolicy.from_orm(p) for p in policies]
        
        # Create evaluation context
        ctx = RCPEvaluationContext(
            algo_key=request.algo_key,
            metrics=request.ctx.get("metrics", {}),
            segment_data=request.ctx.get("segment_data", {}),
            user_role=role,
            manual_override_active=request.ctx.get("manual_override_active", False)
        )
        
        # Evaluate policies
        result = evaluator.evaluate_policies(ctx, policy_schemas, request.actions)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Preview evaluation failed: {str(e)}")


@router.get("/evaluations", response_model=RCPEvaluationList)
async def list_evaluations(
    policy_id: Optional[str] = Query(None, description="Filter by policy ID"),
    algo_key: Optional[str] = Query(None, description="Filter by algorithm"),
    since: Optional[datetime] = Query(None, description="Filter by date"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    role: str = Depends(get_user_role)
):
    """List RCP evaluations with optional filtering."""
    if not check_rcp_permissions(role, "read"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    repo = RCPRepository(db)
    skip = (page - 1) * per_page
    
    evaluations = repo.list_evaluations(
        policy_id=policy_id,
        algo_key=algo_key,
        since=since,
        skip=skip,
        limit=per_page
    )
    
    # Count total for pagination
    total_evaluations = repo.list_evaluations(
        policy_id=policy_id,
        algo_key=algo_key,
        since=since
    )
    
    return RCPEvaluationList(
        evaluations=[RCPEvaluation.from_orm(e) for e in evaluations],
        total=len(total_evaluations),
        page=page,
        per_page=per_page
    )


@router.get("/evaluations/stats")
async def get_evaluation_stats(
    algo_key: Optional[str] = Query(None, description="Filter by algorithm"),
    since: Optional[datetime] = Query(None, description="Filter by date"),
    db: Session = Depends(get_db),
    role: str = Depends(get_user_role)
):
    """Get aggregated evaluation statistics."""
    if not check_rcp_permissions(role, "read"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    repo = RCPRepository(db)
    
    try:
        stats = repo.get_evaluation_stats(algo_key=algo_key, since=since)
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get stats: {str(e)}")


@router.get("/policies/{policy_id}/applicable")
async def check_policy_applicable(
    policy_id: str,
    algo_key: str = Query(..., description="Algorithm to check against"),
    db: Session = Depends(get_db),
    role: str = Depends(get_user_role)
):
    """Check if a policy is applicable to a specific algorithm."""
    if not check_rcp_permissions(role, "read"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    repo = RCPRepository(db)
    policy = repo.get_policy(policy_id)
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    applicable_policies = repo.get_applicable_policies(algo_key)
    is_applicable = any(p.id == policy_id for p in applicable_policies)
    
    return {
        "policy_id": policy_id,
        "algo_key": algo_key,
        "applicable": is_applicable,
        "reason": "Policy matches scope and constraints" if is_applicable else "Policy does not match scope or constraints"
    }
