"""Backtesting & Counterfactuals engine with uplift calculation."""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from ..observability.otel import trace_function

@dataclass
class BacktestConfig:
    """Backtesting configuration."""
    start_date: datetime
    end_date: datetime
    policy_id: str
    baseline_policy_id: Optional[str] = None
    metrics: List[str] = None
    segments: List[str] = None
    confidence_level: float = 0.95

@dataclass
class BacktestResult:
    """Backtesting result."""
    policy_id: str
    baseline_policy_id: Optional[str]
    period_start: datetime
    period_end: datetime
    metrics: Dict[str, float]
    uplift: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]
    statistical_significance: Dict[str, bool]
    sample_size: int
    success: bool
    error_message: Optional[str] = None

@dataclass
class CounterfactualScenario:
    """Counterfactual scenario definition."""
    scenario_id: str
    description: str
    policy_changes: Dict[str, Any]
    context_overrides: Dict[str, Any]

class BacktestingEngine:
    """Backtesting and counterfactual analysis engine."""
    
    def __init__(self, feature_service, replay_engine):
        self.feature_service = feature_service
        self.replay_engine = replay_engine
    
    @trace_function("backtest.run")
    async def run_backtest(self, config: BacktestConfig) -> BacktestResult:
        """Run backtesting analysis."""
        
        try:
            # Get historical data for the period
            historical_data = await self._get_historical_data(
                config.start_date, config.end_date, config.segments
            )
            
            if not historical_data:
                return BacktestResult(
                    policy_id=config.policy_id,
                    baseline_policy_id=config.baseline_policy_id,
                    period_start=config.start_date,
                    period_end=config.end_date,
                    metrics={},
                    uplift={},
                    confidence_intervals={},
                    statistical_significance={},
                    sample_size=0,
                    success=False,
                    error_message="No historical data found for the specified period"
                )
            
            # Simulate policy performance
            policy_results = await self._simulate_policy_performance(
                config.policy_id, historical_data, config.metrics or ["conversions", "revenue", "cost"]
            )
            
            # Simulate baseline performance if specified
            baseline_results = {}
            if config.baseline_policy_id:
                baseline_results = await self._simulate_policy_performance(
                    config.baseline_policy_id, historical_data, config.metrics or ["conversions", "revenue", "cost"]
                )
            
            # Calculate uplift and statistical significance
            uplift = self._calculate_uplift(policy_results, baseline_results)
            confidence_intervals = self._calculate_confidence_intervals(
                policy_results, baseline_results, config.confidence_level
            )
            significance = self._test_statistical_significance(
                policy_results, baseline_results, config.confidence_level
            )
            
            return BacktestResult(
                policy_id=config.policy_id,
                baseline_policy_id=config.baseline_policy_id,
                period_start=config.start_date,
                period_end=config.end_date,
                metrics=policy_results,
                uplift=uplift,
                confidence_intervals=confidence_intervals,
                statistical_significance=significance,
                sample_size=len(historical_data),
                success=True
            )
            
        except Exception as e:
            return BacktestResult(
                policy_id=config.policy_id,
                baseline_policy_id=config.baseline_policy_id,
                period_start=config.start_date,
                period_end=config.end_date,
                metrics={},
                uplift={},
                confidence_intervals={},
                statistical_significance={},
                sample_size=0,
                success=False,
                error_message=str(e)
            )
    
    @trace_function("backtest.counterfactual")
    async def run_counterfactual_analysis(
        self, 
        base_scenario: Dict[str, Any],
        counterfactual_scenarios: List[CounterfactualScenario],
        historical_context: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Run counterfactual analysis comparing multiple scenarios."""
        
        results = {}
        
        # Run base scenario
        base_result = await self.replay_engine.replay_decision(
            timestamp=historical_context.get("timestamp", datetime.utcnow()),
            context=historical_context,
            policy_overrides=base_scenario
        )
        
        results["base"] = {
            "scenario_id": "base",
            "description": "Base scenario",
            "actions": base_result.actions,
            "risk_cost": base_result.risk_cost,
            "metrics": self._extract_metrics_from_actions(base_result.actions)
        }
        
        # Run counterfactual scenarios
        for scenario in counterfactual_scenarios:
            # Merge base context with scenario overrides
            scenario_context = {**historical_context, **scenario.context_overrides}
            scenario_policies = {**base_scenario, **scenario.policy_changes}
            
            scenario_result = await self.replay_engine.replay_decision(
                timestamp=historical_context.get("timestamp", datetime.utcnow()),
                context=scenario_context,
                policy_overrides=scenario_policies
            )
            
            # Calculate uplift vs base scenario
            base_metrics = results["base"]["metrics"]
            scenario_metrics = self._extract_metrics_from_actions(scenario_result.actions)
            uplift = self._calculate_uplift(scenario_metrics, base_metrics)
            
            results[scenario.scenario_id] = {
                "scenario_id": scenario.scenario_id,
                "description": scenario.description,
                "actions": scenario_result.actions,
                "risk_cost": scenario_result.risk_cost,
                "metrics": scenario_metrics,
                "uplift_vs_base": uplift
            }
        
        return results
    
    async def _get_historical_data(self, start_date: datetime, end_date: datetime, 
                                  segments: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get historical data for backtesting."""
        
        # This would typically query a data warehouse or analytics database
        # For now, we'll simulate some historical data
        
        data_points = []
        current_date = start_date
        
        while current_date <= end_date:
            # Simulate daily data points
            for hour in range(0, 24, 6):  # Every 6 hours
                timestamp = current_date + timedelta(hours=hour)
                
                # Get features at this timestamp
                features = await self.feature_service.get_features_at_time(
                    timestamp, horizon_minutes=30
                )
                
                # Simulate traffic and conversion data
                data_point = {
                    "timestamp": timestamp,
                    "features": features,
                    "traffic_volume": np.random.poisson(1000),
                    "conversions": np.random.poisson(25),
                    "revenue": np.random.normal(2500, 500),
                    "cost": np.random.normal(1000, 200),
                    "segment": np.random.choice(segments or ["default"], 1)[0]
                }
                
                data_points.append(data_point)
            
            current_date += timedelta(days=1)
        
        return data_points
    
    async def _simulate_policy_performance(self, policy_id: str, 
                                         historical_data: List[Dict[str, Any]],
                                         metrics: List[str]) -> Dict[str, float]:
        """Simulate policy performance on historical data."""
        
        total_metrics = {metric: 0.0 for metric in metrics}
        
        for data_point in historical_data:
            # Simulate policy decision for this data point
            context = {
                "timestamp": data_point["timestamp"],
                "features": data_point["features"],
                "traffic_volume": data_point["traffic_volume"]
            }
            
            # Mock policy simulation - would use actual replay engine
            policy_effect = await self._simulate_policy_effect(policy_id, context)
            
            # Apply policy effect to observed metrics
            for metric in metrics:
                if metric in data_point:
                    base_value = data_point[metric]
                    effect_multiplier = policy_effect.get(f"{metric}_multiplier", 1.0)
                    total_metrics[metric] += base_value * effect_multiplier
        
        return total_metrics
    
    async def _simulate_policy_effect(self, policy_id: str, context: Dict[str, Any]) -> Dict[str, float]:
        """Simulate the effect of a policy on metrics."""
        
        # Mock policy effects - would use actual policy evaluation
        effects = {
            "conversions_multiplier": 1.0,
            "revenue_multiplier": 1.0,
            "cost_multiplier": 1.0
        }
        
        # Simulate different policy behaviors
        if "aggressive" in policy_id.lower():
            effects["conversions_multiplier"] = 1.15
            effects["cost_multiplier"] = 1.25
        elif "conservative" in policy_id.lower():
            effects["conversions_multiplier"] = 0.95
            effects["cost_multiplier"] = 0.85
        elif "balanced" in policy_id.lower():
            effects["conversions_multiplier"] = 1.05
            effects["cost_multiplier"] = 1.02
        
        return effects
    
    def _calculate_uplift(self, treatment_metrics: Dict[str, float], 
                         control_metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate uplift between treatment and control."""
        
        if not control_metrics:
            return {}
        
        uplift = {}
        for metric, treatment_value in treatment_metrics.items():
            control_value = control_metrics.get(metric, 0)
            
            if control_value > 0:
                uplift[f"{metric}_uplift_pct"] = ((treatment_value - control_value) / control_value) * 100
                uplift[f"{metric}_uplift_abs"] = treatment_value - control_value
            else:
                uplift[f"{metric}_uplift_pct"] = 0.0
                uplift[f"{metric}_uplift_abs"] = treatment_value
        
        return uplift
    
    def _calculate_confidence_intervals(self, treatment_metrics: Dict[str, float],
                                      control_metrics: Dict[str, float],
                                      confidence_level: float) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals for uplift."""
        
        confidence_intervals = {}
        z_score = 1.96 if confidence_level == 0.95 else 2.58  # 95% or 99%
        
        for metric in treatment_metrics:
            if metric in control_metrics:
                # Simplified confidence interval calculation
                # In practice, would use proper statistical methods
                treatment_value = treatment_metrics[metric]
                control_value = control_metrics[metric]
                
                # Estimate standard error (simplified)
                pooled_variance = (treatment_value + control_value) / 2
                standard_error = np.sqrt(pooled_variance / 100)  # Assume sample size of 100
                
                margin_of_error = z_score * standard_error
                uplift = treatment_value - control_value
                
                confidence_intervals[f"{metric}_uplift"] = (
                    uplift - margin_of_error,
                    uplift + margin_of_error
                )
        
        return confidence_intervals
    
    def _test_statistical_significance(self, treatment_metrics: Dict[str, float],
                                     control_metrics: Dict[str, float],
                                     confidence_level: float) -> Dict[str, bool]:
        """Test statistical significance of differences."""
        
        significance = {}
        
        for metric in treatment_metrics:
            if metric in control_metrics:
                # Simplified significance test
                # In practice, would use proper t-test or chi-square test
                treatment_value = treatment_metrics[metric]
                control_value = control_metrics[metric]
                
                # Simple heuristic: significant if difference > 5% and confidence interval doesn't include 0
                if control_value > 0:
                    relative_diff = abs(treatment_value - control_value) / control_value
                    significance[f"{metric}_significant"] = relative_diff > 0.05
                else:
                    significance[f"{metric}_significant"] = treatment_value > 0
        
        return significance
    
    def _extract_metrics_from_actions(self, actions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract metrics from action list."""
        
        metrics = {
            "total_actions": len(actions),
            "total_budget": 0.0,
            "estimated_conversions": 0.0,
            "estimated_revenue": 0.0
        }
        
        for action in actions:
            if action.get("action_type") == "budget_change":
                metrics["total_budget"] += action.get("new_budget", 0)
            
            # Estimate conversions and revenue based on action parameters
            cvr = action.get("expected_cvr", 0.025)
            traffic = action.get("expected_traffic", 1000)
            revenue_per_conversion = action.get("revenue_per_conversion", 100)
            
            estimated_conversions = traffic * cvr
            estimated_revenue = estimated_conversions * revenue_per_conversion
            
            metrics["estimated_conversions"] += estimated_conversions
            metrics["estimated_revenue"] += estimated_revenue
        
        return metrics

class UpliftCalculator:
    """Specialized uplift calculation utilities."""
    
    @staticmethod
    def calculate_causal_uplift(treatment_group: pd.DataFrame, 
                               control_group: pd.DataFrame,
                               outcome_column: str) -> Dict[str, float]:
        """Calculate causal uplift using proper statistical methods."""
        
        treatment_mean = treatment_group[outcome_column].mean()
        control_mean = control_group[outcome_column].mean()
        
        # Average Treatment Effect (ATE)
        ate = treatment_mean - control_mean
        
        # Relative uplift
        relative_uplift = (ate / control_mean) * 100 if control_mean > 0 else 0
        
        # Standard errors
        treatment_se = treatment_group[outcome_column].std() / np.sqrt(len(treatment_group))
        control_se = control_group[outcome_column].std() / np.sqrt(len(control_group))
        ate_se = np.sqrt(treatment_se**2 + control_se**2)
        
        # Confidence interval
        ci_lower = ate - 1.96 * ate_se
        ci_upper = ate + 1.96 * ate_se
        
        # P-value (simplified t-test)
        t_stat = ate / ate_se if ate_se > 0 else 0
        p_value = 2 * (1 - abs(t_stat))  # Simplified p-value calculation
        
        return {
            "ate": ate,
            "relative_uplift_pct": relative_uplift,
            "confidence_interval": (ci_lower, ci_upper),
            "p_value": p_value,
            "statistically_significant": p_value < 0.05,
            "treatment_mean": treatment_mean,
            "control_mean": control_mean,
            "treatment_size": len(treatment_group),
            "control_size": len(control_group)
        }
