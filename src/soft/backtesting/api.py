"""Backtesting & Counterfactuals API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Dict, List, Any, Optional
from datetime import datetime

from .engine import BacktestingEngine, BacktestConfig, CounterfactualScenario
from ..features.service import FeatureService
from ..replay.engine import ReplayEngine
from ..db import SessionLocal

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
from ..observability.otel import trace_function
from sqlalchemy.orm import Session

router = APIRouter()

def check_role(x_role: str = Header(None)):
    """Check user role for RBAC."""
    if not x_role or x_role not in ["viewer", "operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Invalid or missing role")
    return x_role

def get_backtesting_engine(db: Session = Depends(get_db)) -> BacktestingEngine:
    """Get backtesting engine instance."""
    feature_service = FeatureService(db)
    replay_engine = ReplayEngine(db)
    return BacktestingEngine(feature_service, replay_engine)

@router.post("/backtest/run")
@trace_function("api.backtest.run")
async def run_backtest(
    config: Dict[str, Any],
    role: str = Depends(check_role),
    engine: BacktestingEngine = Depends(get_backtesting_engine)
):
    """Run backtesting analysis."""
    if role not in ["operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Parse config
    backtest_config = BacktestConfig(
        start_date=datetime.fromisoformat(config["start_date"]),
        end_date=datetime.fromisoformat(config["end_date"]),
        policy_id=config["policy_id"],
        baseline_policy_id=config.get("baseline_policy_id"),
        metrics=config.get("metrics"),
        segments=config.get("segments"),
        confidence_level=config.get("confidence_level", 0.95)
    )
    
    result = await engine.run_backtest(backtest_config)
    
    return {
        "success": result.success,
        "policy_id": result.policy_id,
        "baseline_policy_id": result.baseline_policy_id,
        "period_start": result.period_start.isoformat(),
        "period_end": result.period_end.isoformat(),
        "metrics": result.metrics,
        "uplift": result.uplift,
        "confidence_intervals": result.confidence_intervals,
        "statistical_significance": result.statistical_significance,
        "sample_size": result.sample_size,
        "error_message": result.error_message
    }

@router.post("/backtest/counterfactual")
@trace_function("api.backtest.counterfactual")
async def run_counterfactual_analysis(
    base_scenario: Dict[str, Any],
    counterfactual_scenarios: List[Dict[str, Any]],
    historical_context: Dict[str, Any],
    role: str = Depends(check_role),
    engine: BacktestingEngine = Depends(get_backtesting_engine)
):
    """Run counterfactual analysis."""
    if role not in ["operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Parse scenarios
    scenarios = [
        CounterfactualScenario(
            scenario_id=s["scenario_id"],
            description=s["description"],
            policy_changes=s["policy_changes"],
            context_overrides=s["context_overrides"]
        )
        for s in counterfactual_scenarios
    ]
    
    results = await engine.run_counterfactual_analysis(
        base_scenario, scenarios, historical_context
    )
    
    return {"results": results}

@router.get("/backtest/templates")
async def get_backtest_templates(role: str = Depends(check_role)):
    """Get backtesting configuration templates."""
    return {
        "templates": [
            {
                "name": "policy_comparison",
                "description": "Compare two policies over a time period",
                "config": {
                    "start_date": "2024-01-01T00:00:00",
                    "end_date": "2024-01-31T23:59:59",
                    "policy_id": "new_policy",
                    "baseline_policy_id": "current_policy",
                    "metrics": ["conversions", "revenue", "cost"],
                    "confidence_level": 0.95
                }
            },
            {
                "name": "uplift_analysis",
                "description": "Analyze uplift of a policy vs no policy",
                "config": {
                    "start_date": "2024-01-01T00:00:00",
                    "end_date": "2024-01-31T23:59:59",
                    "policy_id": "test_policy",
                    "baseline_policy_id": None,
                    "metrics": ["conversions", "revenue"],
                    "confidence_level": 0.95
                }
            }
        ]
    }
