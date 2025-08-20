"""Budget Arbitrage optimizer using OR-Tools LP/QP solver."""

import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from ortools.linear_solver import pywraplp
from ..observability.otel import trace_function

@dataclass
class OptimizationConstraint:
    """Optimization constraint definition."""
    name: str
    type: str  # "equality", "inequality"
    coefficients: Dict[str, float]
    bound: float

@dataclass
class OptimizationResult:
    """Optimization result."""
    success: bool
    objective_value: float
    variables: Dict[str, float]
    solver_status: str
    solve_time_ms: float
    constraints_satisfied: bool
    fallback_used: bool = False

class BudgetArbitrageOptimizer:
    """Budget arbitrage optimizer using OR-Tools."""
    
    def __init__(self, solver_timeout_s: float = 0.5):
        self.solver_timeout_s = solver_timeout_s
    
    @trace_function("optimizer.solve")
    async def optimize_budget_allocation(
        self,
        candidates: List[Dict[str, Any]],
        total_budget: float,
        constraints: Dict[str, Any],
        objective: str = "maximize_conversions"
    ) -> OptimizationResult:
        """Optimize budget allocation across candidates."""
        
        start_time = time.time()
        
        try:
            # Create solver
            solver = pywraplp.Solver.CreateSolver('SCIP')
            if not solver:
                return self._fallback_solution(candidates, total_budget, start_time)
            
            # Set timeout
            solver.SetTimeLimit(int(self.solver_timeout_s * 1000))
            
            # Create variables
            variables = {}
            for i, candidate in enumerate(candidates):
                var_name = f"budget_{candidate.get('id', i)}"
                min_budget = candidate.get('min_budget', 0)
                max_budget = candidate.get('max_budget', total_budget)
                variables[var_name] = solver.NumVar(min_budget, max_budget, var_name)
            
            # Budget constraint: sum of all budgets = total_budget
            budget_constraint = solver.Constraint(total_budget, total_budget, 'total_budget')
            for var in variables.values():
                budget_constraint.SetCoefficient(var, 1.0)
            
            # ROI constraints
            min_roi = constraints.get('min_roi', 0.0)
            if min_roi > 0:
                for i, candidate in enumerate(candidates):
                    var_name = f"budget_{candidate.get('id', i)}"
                    expected_roi = candidate.get('expected_roi', 0.0)
                    if expected_roi < min_roi:
                        # Force this candidate to have zero budget
                        roi_constraint = solver.Constraint(0, 0, f'roi_{var_name}')
                        roi_constraint.SetCoefficient(variables[var_name], 1.0)
            
            # Reallocation step constraints
            max_step = constraints.get('max_reallocation_step', 0.1)
            for i, candidate in enumerate(candidates):
                var_name = f"budget_{candidate.get('id', i)}"
                current_budget = candidate.get('current_budget', 0.0)
                
                # Limit change from current allocation
                max_change = current_budget * max_step
                min_new_budget = max(0, current_budget - max_change)
                max_new_budget = min(total_budget, current_budget + max_change)
                
                # Update variable bounds
                variables[var_name].SetBounds(min_new_budget, max_new_budget)
            
            # Movement frequency constraints
            max_moves_per_hour = constraints.get('max_moves_per_hour', 10)
            # This would require historical data - simplified for now
            
            # Set objective
            objective_expr = solver.Objective()
            
            if objective == "maximize_conversions":
                for i, candidate in enumerate(candidates):
                    var_name = f"budget_{candidate.get('id', i)}"
                    conversion_rate = candidate.get('conversion_rate', 0.0)
                    cost_per_click = candidate.get('cost_per_click', 1.0)
                    
                    # Conversions = (budget / cost_per_click) * conversion_rate
                    conversion_coefficient = conversion_rate / cost_per_click if cost_per_click > 0 else 0
                    objective_expr.SetCoefficient(variables[var_name], conversion_coefficient)
                
                objective_expr.SetMaximization()
            
            elif objective == "maximize_revenue":
                for i, candidate in enumerate(candidates):
                    var_name = f"budget_{candidate.get('id', i)}"
                    revenue_per_conversion = candidate.get('revenue_per_conversion', 0.0)
                    conversion_rate = candidate.get('conversion_rate', 0.0)
                    cost_per_click = candidate.get('cost_per_click', 1.0)
                    
                    # Revenue = conversions * revenue_per_conversion
                    revenue_coefficient = (conversion_rate * revenue_per_conversion) / cost_per_click if cost_per_click > 0 else 0
                    objective_expr.SetCoefficient(variables[var_name], revenue_coefficient)
                
                objective_expr.SetMaximization()
            
            # Solve
            status = solver.Solve()
            solve_time_ms = (time.time() - start_time) * 1000
            
            if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
                # Extract solution
                solution = {}
                for var_name, var in variables.items():
                    solution[var_name] = var.solution_value()
                
                return OptimizationResult(
                    success=True,
                    objective_value=solver.Objective().Value(),
                    variables=solution,
                    solver_status=self._get_status_string(status),
                    solve_time_ms=solve_time_ms,
                    constraints_satisfied=True
                )
            
            else:
                # Solver failed, use fallback
                return self._fallback_solution(candidates, total_budget, start_time)
        
        except Exception as e:
            # Error occurred, use fallback
            return self._fallback_solution(candidates, total_budget, start_time, str(e))
    
    def _fallback_solution(self, candidates: List[Dict[str, Any]], 
                          total_budget: float, start_time: float, 
                          error: str = None) -> OptimizationResult:
        """Fallback heuristic solution."""
        solve_time_ms = (time.time() - start_time) * 1000
        
        # Simple heuristic: allocate based on expected ROI
        roi_scores = []
        for i, candidate in enumerate(candidates):
            roi = candidate.get('expected_roi', 0.0)
            roi_scores.append((i, roi))
        
        # Sort by ROI descending
        roi_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Allocate budget proportionally to ROI
        total_roi = sum(score[1] for score in roi_scores if score[1] > 0)
        
        solution = {}
        if total_roi > 0:
            for i, candidate in enumerate(candidates):
                var_name = f"budget_{candidate.get('id', i)}"
                roi = candidate.get('expected_roi', 0.0)
                if roi > 0:
                    allocation = (roi / total_roi) * total_budget
                    # Apply min/max constraints
                    min_budget = candidate.get('min_budget', 0)
                    max_budget = candidate.get('max_budget', total_budget)
                    solution[var_name] = max(min_budget, min(max_budget, allocation))
                else:
                    solution[var_name] = candidate.get('min_budget', 0)
        else:
            # Equal allocation if no ROI data
            budget_per_candidate = total_budget / len(candidates)
            for i, candidate in enumerate(candidates):
                var_name = f"budget_{candidate.get('id', i)}"
                solution[var_name] = budget_per_candidate
        
        # Normalize to total budget
        current_total = sum(solution.values())
        if current_total > 0:
            for var_name in solution:
                solution[var_name] = (solution[var_name] / current_total) * total_budget
        
        # Calculate objective value (approximate)
        objective_value = 0.0
        for i, candidate in enumerate(candidates):
            var_name = f"budget_{candidate.get('id', i)}"
            budget = solution[var_name]
            conversion_rate = candidate.get('conversion_rate', 0.0)
            cost_per_click = candidate.get('cost_per_click', 1.0)
            if cost_per_click > 0:
                conversions = (budget / cost_per_click) * conversion_rate
                objective_value += conversions
        
        return OptimizationResult(
            success=True,
            objective_value=objective_value,
            variables=solution,
            solver_status="FALLBACK_HEURISTIC",
            solve_time_ms=solve_time_ms,
            constraints_satisfied=True,
            fallback_used=True
        )
    
    def _get_status_string(self, status: int) -> str:
        """Convert solver status to string."""
        status_map = {
            pywraplp.Solver.OPTIMAL: "OPTIMAL",
            pywraplp.Solver.FEASIBLE: "FEASIBLE",
            pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
            pywraplp.Solver.UNBOUNDED: "UNBOUNDED",
            pywraplp.Solver.ABNORMAL: "ABNORMAL",
            pywraplp.Solver.NOT_SOLVED: "NOT_SOLVED"
        }
        return status_map.get(status, "UNKNOWN")

class WeightOptimizer:
    """Weight optimization for traffic routing."""
    
    def __init__(self, solver_timeout_s: float = 0.5):
        self.solver_timeout_s = solver_timeout_s
    
    @trace_function("optimizer.weights")
    async def optimize_weights(
        self,
        destinations: List[Dict[str, Any]],
        constraints: Dict[str, Any],
        objective: str = "maximize_conversions"
    ) -> OptimizationResult:
        """Optimize traffic weights across destinations."""
        
        start_time = time.time()
        
        try:
            solver = pywraplp.Solver.CreateSolver('SCIP')
            if not solver:
                return self._fallback_weight_solution(destinations, start_time)
            
            solver.SetTimeLimit(int(self.solver_timeout_s * 1000))
            
            # Create weight variables
            variables = {}
            for i, dest in enumerate(destinations):
                var_name = f"weight_{dest.get('id', i)}"
                min_weight = dest.get('min_weight', 0.01)
                max_weight = dest.get('max_weight', 0.8)
                variables[var_name] = solver.NumVar(min_weight, max_weight, var_name)
            
            # Sum of weights = 1
            weight_sum_constraint = solver.Constraint(1.0, 1.0, 'weight_sum')
            for var in variables.values():
                weight_sum_constraint.SetCoefficient(var, 1.0)
            
            # Weight delta constraints
            max_delta = constraints.get('max_weight_delta', 0.15)
            for i, dest in enumerate(destinations):
                var_name = f"weight_{dest.get('id', i)}"
                current_weight = dest.get('current_weight', 0.1)
                
                # Limit change from current weight
                min_new_weight = max(0.01, current_weight - max_delta)
                max_new_weight = min(0.8, current_weight + max_delta)
                
                variables[var_name].SetBounds(min_new_weight, max_new_weight)
            
            # Set objective
            objective_expr = solver.Objective()
            
            if objective == "maximize_conversions":
                for i, dest in enumerate(destinations):
                    var_name = f"weight_{dest.get('id', i)}"
                    conversion_rate = dest.get('conversion_rate', 0.0)
                    traffic_volume = dest.get('expected_traffic', 1000)
                    
                    # Expected conversions = weight * traffic_volume * conversion_rate
                    conversion_coefficient = traffic_volume * conversion_rate
                    objective_expr.SetCoefficient(variables[var_name], conversion_coefficient)
                
                objective_expr.SetMaximization()
            
            # Solve
            status = solver.Solve()
            solve_time_ms = (time.time() - start_time) * 1000
            
            if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
                solution = {}
                for var_name, var in variables.items():
                    solution[var_name] = var.solution_value()
                
                return OptimizationResult(
                    success=True,
                    objective_value=solver.Objective().Value(),
                    variables=solution,
                    solver_status=self._get_status_string(status),
                    solve_time_ms=solve_time_ms,
                    constraints_satisfied=True
                )
            
            else:
                return self._fallback_weight_solution(destinations, start_time)
        
        except Exception as e:
            return self._fallback_weight_solution(destinations, start_time, str(e))
    
    def _fallback_weight_solution(self, destinations: List[Dict[str, Any]], 
                                 start_time: float, error: str = None) -> OptimizationResult:
        """Fallback weight allocation."""
        solve_time_ms = (time.time() - start_time) * 1000
        
        # Allocate based on conversion rates
        conversion_rates = []
        for i, dest in enumerate(destinations):
            rate = dest.get('conversion_rate', 0.0)
            conversion_rates.append((i, rate))
        
        total_rate = sum(rate[1] for rate in conversion_rates if rate[1] > 0)
        
        solution = {}
        if total_rate > 0:
            for i, dest in enumerate(destinations):
                var_name = f"weight_{dest.get('id', i)}"
                rate = dest.get('conversion_rate', 0.0)
                if rate > 0:
                    weight = rate / total_rate
                    # Apply bounds
                    min_weight = dest.get('min_weight', 0.01)
                    max_weight = dest.get('max_weight', 0.8)
                    solution[var_name] = max(min_weight, min(max_weight, weight))
                else:
                    solution[var_name] = dest.get('min_weight', 0.01)
        else:
            # Equal weights
            weight_per_dest = 1.0 / len(destinations)
            for i, dest in enumerate(destinations):
                var_name = f"weight_{dest.get('id', i)}"
                solution[var_name] = weight_per_dest
        
        # Normalize to sum = 1
        current_total = sum(solution.values())
        if current_total > 0:
            for var_name in solution:
                solution[var_name] = solution[var_name] / current_total
        
        return OptimizationResult(
            success=True,
            objective_value=0.0,
            variables=solution,
            solver_status="FALLBACK_HEURISTIC",
            solve_time_ms=solve_time_ms,
            constraints_satisfied=True,
            fallback_used=True
        )
    
    def _get_status_string(self, status: int) -> str:
        """Convert solver status to string."""
        status_map = {
            pywraplp.Solver.OPTIMAL: "OPTIMAL",
            pywraplp.Solver.FEASIBLE: "FEASIBLE",
            pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
            pywraplp.Solver.UNBOUNDED: "UNBOUNDED",
            pywraplp.Solver.ABNORMAL: "ABNORMAL",
            pywraplp.Solver.NOT_SOLVED: "NOT_SOLVED"
        }
        return status_map.get(status, "UNKNOWN")
