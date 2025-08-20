"""Replay and What-If simulation API endpoints."""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from .engine import ReplayEngine, WhatIfSimulator, ShadowRunner
from ..pac.schemas import (
    DecisionGraph, ReplayRequest, WhatIfRequest, ShadowRunConfig
)
from ..db import SessionLocal

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# from ..auth import get_current_user_role  # Comment out if auth module doesn't exist
# from ..rcp.evaluator import RCPEvaluator  # Comment out if module doesn't exist
from ..features.service import FeatureService

router = APIRouter(prefix="/replay", tags=["Replay & Simulation"])

def get_replay_engine(db: Session = Depends(get_db)) -> ReplayEngine:
    """Get replay engine instance."""
    # rcp_evaluator = RCPEvaluator()  # Comment out if module doesn't exist
    feature_service = FeatureService(db)
    return ReplayEngine(db)

def get_whatif_simulator(db: Session = Depends(get_db)) -> WhatIfSimulator:
    """Get what-if simulator instance."""
    # rcp_evaluator = RCPEvaluator()  # Comment out if module doesn't exist
    feature_service = FeatureService(db)
    return WhatIfSimulator(db)

def get_shadow_runner() -> ShadowRunner:
    """Get shadow runner instance."""
    # rcp_evaluator = RCPEvaluator()  # Comment out if module doesn't exist
    return ShadowRunner()

@router.get("/graph", response_model=DecisionGraph)
async def get_decision_graph(
    algo_key: str,
    ts: str,
    horizon_min: int = 60,
    replay_engine: ReplayEngine = Depends(get_replay_engine),
    x_role: str = Header(None)
):
    """Get decision graph for a specific timestamp."""
    from datetime import datetime
    
    try:
        timestamp = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format")
    
    request = ReplayRequest(
        algo_key=algo_key,
        timestamp=timestamp,
        horizon_minutes=horizon_min
    )
    
    graph = await replay_engine.replay_decision(request)
    return graph

@router.post("/run", response_model=DecisionGraph)
async def replay_run(
    request: ReplayRequest,
    replay_engine: ReplayEngine = Depends(get_replay_engine),
    role: str = Depends(get_current_user_role)
):
    """Simulate a run with frozen context."""
    graph = await replay_engine.replay_decision(request)
    return graph

@router.post("/whatif", response_model=Dict[str, Any])
async def simulate_whatif(
    request: WhatIfRequest,
    simulator: WhatIfSimulator = Depends(get_whatif_simulator),
    role: str = Depends(get_current_user_role)
):
    """Run what-if simulation with sliders."""
    result = await simulator.simulate(request)
    return result

@router.post("/shadow/enable")
async def enable_shadow_run(
    config: ShadowRunConfig,
    shadow_runner: ShadowRunner = Depends(get_shadow_runner),
    role: str = Depends(get_current_user_role)
):
    """Enable shadow run mode."""
    if role not in ["admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    await shadow_runner.enable_shadow(
        algo_key=config.algo_key,
        duration_minutes=config.duration_minutes,
        sample_rate=config.sample_rate
    )
    
    return {"success": True, "message": f"Shadow mode enabled for {config.algo_key}"}

@router.post("/shadow/disable")
async def disable_shadow_run(
    algo_key: str,
    shadow_runner: ShadowRunner = Depends(get_shadow_runner),
    role: str = Depends(get_current_user_role)
):
    """Disable shadow run mode."""
    if role not in ["admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    await shadow_runner.disable_shadow(algo_key)
    return {"success": True, "message": f"Shadow mode disabled for {algo_key}"}

@router.get("/shadow/status")
async def get_shadow_status(
    algo_key: str,
    shadow_runner: ShadowRunner = Depends(get_shadow_runner),
    role: str = Depends(get_current_user_role)
):
    """Get shadow run status."""
    status = shadow_runner.get_shadow_status(algo_key)
    return status
