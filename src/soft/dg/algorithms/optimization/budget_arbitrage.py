"""
Budget Arbitrage Algorithm for SmartLinks Autonomous DG.

This algorithm dynamically allocates budgets across campaigns and traffic sources
to maximize return on ad spend (ROAS) while respecting constraints.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from scipy.optimize import minimize

from ...models.decision import Action, DecisionContext
from ..base import Algorithm, AlgorithmResult

logger = logging.getLogger(__name__)

class BudgetArbitrageAlgorithm(Algorithm):
    """Algorithm for dynamic budget allocation across campaigns."""
    
    # Default configuration
    DEFAULT_CONFIG = {
        "min_budget_ratio": 0.1,  # Minimum budget as ratio of current budget
        "max_budget_ratio": 5.0,  # Maximum budget as ratio of current budget
        "learning_rate": 0.1,     # How aggressively to adjust budgets
        "lookback_days": 7,       # How many days of history to consider
        "min_roi_threshold": 1.0, # Minimum ROI to consider a campaign viable
        "max_daily_change_pct": 20,  # Max % change in daily budget
        "min_budget": 1.0,        # Minimum budget amount (absolute)
        "max_iterations": 100,    # Max optimization iterations
        "constraints": {
            "total_budget": None,  # Will be set at runtime
            "min_impressions": 1000,  # Minimum impressions per day per campaign
            "max_cpc": 5.0,       # Maximum CPC in currency units
        },
        "metrics": {
            "roi_window": 24,     # Hours to calculate ROI over
            "conversion_window": 24,  # Hours to attribute conversions
            "decay_rate": 0.5,    # Exponential decay rate for older data
        }
    }
    
    @classmethod
    def get_name(cls) -> str:
        return "budget_arbitrage"
    
    def __init__(self):
        self.history = []
        self.last_optimized = None
    
    async def execute(self, context: DecisionContext, 
                     config: Optional[Dict[str, Any]] = None) -> AlgorithmResult:
        """Execute the budget arbitrage algorithm.
        
        Args:
            context: Current decision context
            config: Algorithm configuration (overrides defaults)
            
        Returns:
            AlgorithmResult containing budget allocation recommendations
        """
        # Merge default config with provided config
        config = {**self.DEFAULT_CONFIG, **(config or {})}
        
        try:
            # Update historical data
            self._update_history(context)
            
            # Only optimize periodically (e.g., once per hour)
            if not self._should_optimize():
                return AlgorithmResult(
                    algorithm_name=self.get_name(),
                    confidence=0.0,
                    recommended_actions=[],
                    metadata={"status": "optimization_not_needed"}
                )
            
            # Get current campaigns and performance
            campaigns = self._get_active_campaigns(context)
            if not campaigns:
                logger.warning("No active campaigns found for budget optimization")
                return AlgorithmResult(
                    algorithm_name=self.get_name(),
                    confidence=0.0,
                    recommended_actions=[],
                    metadata={"status": "no_active_campaigns"}
                )
            
            # Calculate performance metrics
            campaign_metrics = self._calculate_campaign_metrics(campaigns, config)
            
            # Optimize budget allocation
            optimized_budgets = self._optimize_budgets(campaign_metrics, config)
            
            # Generate actions for budget adjustments
            actions = self._generate_budget_actions(optimized_budgets, campaign_metrics, config)
            
            # Calculate confidence based on data quality and optimization results
            confidence = self._calculate_confidence(campaign_metrics, optimized_budgets)
            
            # Prepare metadata
            metadata = {
                "campaign_count": len(campaigns),
                "total_budget": sum(b["current_budget"] for b in campaign_metrics.values()),
                "optimized_budget": sum(optimized_budgets.values()),
                "timestamp": datetime.utcnow().isoformat(),
                "campaign_metrics": campaign_metrics,
                "optimized_budgets": optimized_budgets
            }
            
            return AlgorithmResult(
                algorithm_name=self.get_name(),
                confidence=confidence,
                recommended_actions=actions,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error in budget arbitrage: {e}", exc_info=True)
            return AlgorithmResult(
                algorithm_name=self.get_name(),
                confidence=0.0,
                recommended_actions=[],
                metadata={"error": str(e), "timestamp": datetime.utcnow().isoformat()}
            )
    
    def _update_history(self, context: DecisionContext) -> None:
        """Update historical performance data."""
        # In a real implementation, this would store historical data
        # For now, we'll just track the last update time
        self.last_optimized = datetime.utcnow()
    
    def _should_optimize(self) -> bool:
        """Determine if optimization should run now."""
        if self.last_optimized is None:
            return True
        # Optimize at most once per hour
        return (datetime.utcnow() - self.last_optimized) > timedelta(hours=1)
    
    def _get_active_campaigns(self, context: DecisionContext) -> List[Dict[str, Any]]:
        """Get list of active campaigns from context."""
        # In a real implementation, this would query the database or API
        # For now, return mock data
        return [
            {
                "id": "campaign_1",
                "name": "US Mobile Traffic",
                "daily_budget": 1000.0,
                "status": "active",
                "target_roas": 3.0,
                "constraints": {"max_cpc": 2.5, "min_impressions": 1000}
            },
            {
                "id": "campaign_2",
                "name": "EU Desktop Traffic",
                "daily_budget": 800.0,
                "status": "active",
                "target_roas": 2.5,
                "constraints": {"max_cpc": 1.8, "min_impressions": 800}
            },
            {
                "id": "campaign_3",
                "name": "Asia Mobile Traffic",
                "daily_budget": 600.0,
                "status": "active",
                "target_roas": 2.0,
                "constraints": {"max_cpc": 1.2, "min_impressions": 500}
            }
        ]
    
    def _calculate_campaign_metrics(self, campaigns: List[Dict[str, Any]], 
                                  config: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Calculate performance metrics for each campaign."""
        metrics = {}
        
        for campaign in campaigns:
            campaign_id = campaign["id"]
            
            # In a real implementation, this would use historical data
            # For now, generate some mock metrics
            metrics[campaign_id] = {
                "campaign_id": campaign_id,
                "current_budget": campaign["daily_budget"],
                "roi": np.random.uniform(1.5, 4.0),  # Random ROI between 1.5x and 4.0x
                "cpc": campaign["constraints"]["max_cpc"] * np.random.uniform(0.7, 1.0),
                "conversion_rate": np.random.uniform(0.01, 0.05),  # 1-5% conversion rate
                "impressions": max(
                    campaign["constraints"]["min_impressions"],
                    int(campaign["daily_budget"] / campaign["constraints"]["max_cpc"] * np.random.uniform(0.8, 1.2))
                ),
                "target_roi": campaign.get("target_roas", 2.0),
                "min_budget": campaign["daily_budget"] * config["min_budget_ratio"],
                "max_budget": campaign["daily_budget"] * config["max_budget_ratio"],
                "constraints": campaign.get("constraints", {})
            }
        
        return metrics
    
    def _optimize_budgets(self, campaign_metrics: Dict[str, Dict[str, float]],
                         config: Dict[str, Any]) -> Dict[str, float]:
        """Optimize budget allocation across campaigns."""
        # Prepare data for optimization
        campaign_ids = list(campaign_metrics.keys())
        n_campaigns = len(campaign_ids)
        
        if n_campaigns == 0:
            return {}
        
        # Current budgets and constraints
        current_budgets = np.array([campaign_metrics[cid]["current_budget"] for cid in campaign_ids])
        min_budgets = np.array([max(campaign_metrics[cid]["min_budget"], config["min_budget"]) 
                              for cid in campaign_ids])
        max_budgets = np.array([campaign_metrics[cid]["max_budget"] for cid in campaign_ids])
        rois = np.array([campaign_metrics[cid]["roi"] for cid in campaign_ids])
        
        # Total budget constraint (sum of current budgets)
        total_budget = sum(current_budgets)
        
        # Objective function: maximize total profit
        def objective(x):
            # Calculate total return (negative because we minimize)
            total_return = -np.sum(x * rois)
            
            # Add penalty for budget changes (smooth optimization)
            budget_change_penalty = 0.1 * np.sum((x - current_budgets) ** 2) / total_budget
            
            return total_return + budget_change_penalty
        
        # Constraints
        constraints = [
            # Budget must sum to total_budget
            {"type": "eq", "fun": lambda x: np.sum(x) - total_budget},
            # Each campaign's budget must be within bounds
            *[{"type": "ineq", "fun": lambda x, i=i: x[i] - min_budgets[i]} for i in range(n_campaigns)],
            *[{"type": "ineq", "fun": lambda x, i=i: max_budgets[i] - x[i]} for i in range(n_campaigns)]
        ]
        
        # Bounds (0 <= budget <= max_budget for each campaign)
        bounds = [(0, max_b) for max_b in max_budgets]
        
        # Initial guess (current budgets)
        x0 = current_budgets.copy()
        
        # Run optimization
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': config["max_iterations"]}
        )
        
        if not result.success:
            logger.warning(f"Budget optimization failed: {result.message}")
            return {cid: campaign_metrics[cid]["current_budget"] for cid in campaign_ids}
        
        # Return optimized budgets
        return {cid: float(max(0, x)) for cid, x in zip(campaign_ids, result.x)}
    
    def _generate_budget_actions(self, 
                               optimized_budgets: Dict[str, float],
                               campaign_metrics: Dict[str, Dict[str, float]],
                               config: Dict[str, Any]) -> List[Action]:
        """Generate actions to implement the optimized budget allocation."""
        actions = []
        
        for campaign_id, new_budget in optimized_budgets.items():
            current_budget = campaign_metrics[campaign_id]["current_budget"]
            
            # Skip if change is too small
            if abs(new_budget - current_budget) < 0.01:
                continue
            
            # Calculate percentage change
            pct_change = ((new_budget / current_budget) - 1) * 100
            
            # Apply maximum daily change limit
            if abs(pct_change) > config["max_daily_change_pct"]:
                max_change = 1 + (config["max_daily_change_pct"] / 100) * (1 if pct_change > 0 else -1)
                adjusted_budget = current_budget * max_change
                
                action = Action(
                    action_type="adjust_campaign_budget",
                    params={
                        "campaign_id": campaign_id,
                        "new_budget": adjusted_budget,
                        "original_budget": current_budget,
                        "target_budget": new_budget,
                        "reason": f"Budget adjustment capped at {config['max_daily_change_pct']}% daily change"
                    },
                    priority=70,
                    description=f"Adjust budget for campaign {campaign_id} to ${adjusted_budget:.2f} "
                              f"(capped at {config['max_daily_change_pct']}% change)",
                    source_algorithm=self.get_name()
                )
            else:
                action = Action(
                    action_type="adjust_campaign_budget",
                    params={
                        "campaign_id": campaign_id,
                        "new_budget": new_budget,
                        "original_budget": current_budget,
                        "reason": "Optimized budget allocation"
                    },
                    priority=80,
                    description=f"Adjust budget for campaign {campaign_id} from ${current_budget:.2f} to ${new_budget:.2f} "
                              f"({pct_change:+.1f}%)",
                    source_algorithm=self.get_name()
                )
            
            actions.append(action)
        
        # Add a summary action if there are multiple campaigns
        if len(actions) > 1:
            total_budget = sum(b["current_budget"] for b in campaign_metrics.values())
            total_optimized = sum(optimized_budgets.values())
            
            actions.append(Action(
                action_type="log_message",
                params={
                    "level": "info",
                    "message": f"Optimized budget allocation across {len(actions)} campaigns. "
                              f"Total budget: ${total_budget:.2f} → ${total_optimized:.2f}"
                },
                priority=50,
                description="Budget optimization summary",
                source_algorithm=self.get_name()
            ))
        
        return actions
    
    def _calculate_confidence(self, 
                            campaign_metrics: Dict[str, Dict[str, float]],
                            optimized_budgets: Dict[str, float]) -> float:
        """Calculate confidence in the optimization results."""
        if not campaign_metrics or not optimized_budgets:
            return 0.0
        
        # Calculate average ROI (higher ROI = more confidence in optimization)
        avg_roi = np.mean([m["roi"] for m in campaign_metrics.values()])
        roi_confidence = min(1.0, avg_roi / 3.0)  # Cap at 1.0 for ROI >= 3.0
        
        # Calculate data quality score (more data = more confidence)
        total_impressions = sum(m.get("impressions", 0) for m in campaign_metrics.values())
        data_quality = min(1.0, total_impressions / 10000)  # Cap at 1.0 for 10k+ impressions
        
        # Combine factors (equal weight for now)
        confidence = (roi_confidence + data_quality) / 2.0
        
        return max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
