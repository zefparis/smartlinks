"""Feature Store API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..db import SessionLocal

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
from .service import FeatureService
from ..pac.schemas import FeatureSnapshot
from ..observability.otel import trace_function

router = APIRouter()

def get_feature_service(db: Session = Depends(get_db)) -> FeatureService:
    """Get feature service instance."""
    return FeatureService(db)

def check_role(x_role: str = Header(None)):
    """Check user role for RBAC."""
    if not x_role or x_role not in ["viewer", "operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Invalid or missing role")
    return x_role

@router.get("/features/online/{key}")
@trace_function("api.features.get_online")
async def get_online_feature(
    key: str,
    tenant_id: Optional[str] = None,
    role: str = Depends(check_role),
    feature_service: FeatureService = Depends(get_feature_service)
):
    """Get online feature from Redis."""
    feature = await feature_service.get_online_feature(key, tenant_id)
    if feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")
    return {"key": key, "value": feature}

@router.post("/features/online/{key}")
@trace_function("api.features.set_online")
async def set_online_feature(
    key: str,
    value: Dict[str, Any],
    tenant_id: Optional[str] = None,
    role: str = Depends(check_role),
    feature_service: FeatureService = Depends(get_feature_service)
):
    """Set online feature in Redis."""
    if role not in ["operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    await feature_service.set_online_feature(key, value, tenant_id)
    return {"status": "success", "key": key}

@router.post("/features/online/batch")
@trace_function("api.features.get_online_batch")
async def get_online_features_batch(
    keys: List[str],
    tenant_id: Optional[str] = None,
    role: str = Depends(check_role),
    feature_service: FeatureService = Depends(get_feature_service)
):
    """Get multiple online features."""
    features = await feature_service.get_online_features(keys, tenant_id)
    return {"features": features}

@router.post("/features/snapshot")
@trace_function("api.features.snapshot")
async def create_feature_snapshot(
    key: str,
    value: Dict[str, Any],
    source: str,
    tenant_id: Optional[str] = None,
    role: str = Depends(check_role),
    feature_service: FeatureService = Depends(get_feature_service)
):
    """Create offline feature snapshot."""
    if role not in ["operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    snapshot_id = await feature_service.snapshot_feature(key, value, source, tenant_id)
    return {"snapshot_id": snapshot_id}

@router.get("/features/history/{key}")
@trace_function("api.features.history")
async def get_feature_history(
    key: str,
    start_time: datetime,
    end_time: datetime,
    tenant_id: Optional[str] = None,
    role: str = Depends(check_role),
    feature_service: FeatureService = Depends(get_feature_service)
):
    """Get feature history for backtesting."""
    history = await feature_service.get_feature_history(key, start_time, end_time, tenant_id)
    return {"key": key, "history": history}

@router.get("/features/freshness/{key}")
@trace_function("api.features.freshness")
async def check_feature_freshness(
    key: str,
    max_age_minutes: int = 60,
    tenant_id: Optional[str] = None,
    role: str = Depends(check_role),
    feature_service: FeatureService = Depends(get_feature_service)
):
    """Check feature freshness and detect drift."""
    freshness = await feature_service.check_feature_freshness(key, max_age_minutes, tenant_id)
    return freshness
