"""Bandits Traffic Optimizer API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..autopilot.bandits.thompson import BanditTrafficOptimizer
from ..observability.otel import trace_function

router = APIRouter()

# Global bandit optimizers (in production, would be managed per tenant)
bandit_optimizers: Dict[str, BanditTrafficOptimizer] = {}

def check_role(x_role: str = Header(None)):
    """Check user role for RBAC."""
    if not x_role or x_role not in ["viewer", "operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Invalid or missing role")
    return x_role

def get_bandit_optimizer(algo_key: str, algorithm: str = "thompson") -> BanditTrafficOptimizer:
    """Get or create bandit optimizer for algorithm."""
    key = f"{algo_key}_{algorithm}"
    if key not in bandit_optimizers:
        bandit_optimizers[key] = BanditTrafficOptimizer(algorithm=algorithm)
    return bandit_optimizers[key]

@router.post("/bandits/{algo_key}/optimize")
@trace_function("api.bandits.optimize")
async def optimize_traffic(
    algo_key: str,
    destinations: List[str],
    historical_data: Dict[str, Dict],
    constraints: Dict[str, float] = None,
    algorithm: str = "thompson",
    role: str = Depends(check_role)
):
    """Optimize traffic allocation using bandits."""
    if role not in ["operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    optimizer = get_bandit_optimizer(algo_key, algorithm)
    
    weights = await optimizer.optimize_traffic(
        destinations=destinations,
        historical_data=historical_data,
        constraints=constraints or {}
    )
    
    return {
        "algo_key": algo_key,
        "algorithm": algorithm,
        "weights": weights,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/bandits/{algo_key}/stats")
@trace_function("api.bandits.stats")
async def get_bandit_stats(
    algo_key: str,
    algorithm: str = "thompson",
    role: str = Depends(check_role)
):
    """Get bandit algorithm statistics."""
    optimizer = get_bandit_optimizer(algo_key, algorithm)
    stats = optimizer.get_bandit_stats()
    
    return {
        "algo_key": algo_key,
        "algorithm": algorithm,
        "stats": stats
    }

@router.post("/bandits/{algo_key}/update")
@trace_function("api.bandits.update")
async def update_bandit_data(
    algo_key: str,
    destination_id: str,
    data: Dict[str, Any],
    algorithm: str = "thompson",
    role: str = Depends(check_role)
):
    """Update bandit with new performance data."""
    if role not in ["operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    optimizer = get_bandit_optimizer(algo_key, algorithm)
    
    if algorithm == "thompson":
        successes = data.get("conversions", 0)
        total = data.get("visits", 1)
        failures = max(0, total - successes)
        optimizer.bandit.update_arm(destination_id, successes, failures)
    elif algorithm == "ucb":
        reward = data.get("cvr", 0.0)
        optimizer.bandit.update_arm(destination_id, reward)
    
    return {"status": "updated", "destination_id": destination_id}

@router.get("/bandits/algorithms")
async def list_bandit_algorithms(role: str = Depends(check_role)):
    """List available bandit algorithms."""
    return {
        "algorithms": [
            {
                "name": "thompson",
                "description": "Thompson Sampling with Beta-Binomial conjugate prior",
                "use_case": "Good for conversion optimization with binary outcomes"
            },
            {
                "name": "ucb",
                "description": "Upper Confidence Bound with exploration bonus",
                "use_case": "Good for continuous reward optimization"
            }
        ]
    }
