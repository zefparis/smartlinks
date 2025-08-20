"""Budget Optimizer API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..autopilot.planner.optimizer import BudgetArbitrageOptimizer, WeightOptimizer
from ..observability.otel import trace_function

router = APIRouter()

def check_role(x_role: str = Header(None)):
    """Check user role for RBAC."""
    if not x_role or x_role not in ["viewer", "operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Invalid or missing role")
    return x_role

@router.post("/optimizer/budget")
@trace_function("api.optimizer.budget")
async def optimize_budget_allocation(
    candidates: List[Dict[str, Any]],
    total_budget: float,
    constraints: Dict[str, Any] = None,
    objective: str = "maximize_conversions",
    role: str = Depends(check_role)
):
    """Optimize budget allocation using OR-Tools."""
    if role not in ["operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    optimizer = BudgetArbitrageOptimizer()
    
    result = await optimizer.optimize_budget_allocation(
        candidates=candidates,
        total_budget=total_budget,
        constraints=constraints or {},
        objective=objective
    )
    
    return {
        "success": result.success,
        "objective_value": result.objective_value,
        "variables": result.variables,
        "solver_status": result.solver_status,
        "solve_time_ms": result.solve_time_ms,
        "constraints_satisfied": result.constraints_satisfied,
        "fallback_used": result.fallback_used,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/optimizer/weights")
@trace_function("api.optimizer.weights")
async def optimize_traffic_weights(
    destinations: List[Dict[str, Any]],
    constraints: Dict[str, Any] = None,
    objective: str = "maximize_conversions",
    role: str = Depends(check_role)
):
    """Optimize traffic weights using OR-Tools."""
    if role not in ["operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    optimizer = WeightOptimizer()
    
    result = await optimizer.optimize_weights(
        destinations=destinations,
        constraints=constraints or {},
        objective=objective
    )
    
    return {
        "success": result.success,
        "objective_value": result.objective_value,
        "variables": result.variables,
        "solver_status": result.solver_status,
        "solve_time_ms": result.solve_time_ms,
        "constraints_satisfied": result.constraints_satisfied,
        "fallback_used": result.fallback_used,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/optimizer/objectives")
async def list_optimization_objectives(role: str = Depends(check_role)):
    """List available optimization objectives."""
    return {
        "objectives": [
            {
                "name": "maximize_conversions",
                "description": "Maximize total conversions across all candidates"
            },
            {
                "name": "maximize_revenue",
                "description": "Maximize total revenue across all candidates"
            }
        ]
    }
