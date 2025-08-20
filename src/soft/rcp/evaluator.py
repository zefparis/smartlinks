"""
RCP Evaluator - Core logic for evaluating policies against algorithm actions.
"""

import hashlib
import json
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from croniter import croniter
import logging

from .schemas import (
    ActionDTO, RCPPolicy, RCPResult, RCPEvaluationContext,
    RCPEvaluationStats, RCPEvaluationDiff, GateCondition, MutationRule,
    GuardLimits, RateLimits
)

logger = logging.getLogger(__name__)


class RCPEvaluator:
    """
    Runtime Control Policy Evaluator.
    
    Evaluates policies against algorithm actions and returns filtered/modified results.
    """
    
    def __init__(self):
        self.rate_limit_cache: Dict[str, List[datetime]] = {}
    
    def evaluate_policies(
        self, 
        ctx: RCPEvaluationContext, 
        policies: List[RCPPolicy], 
        actions: List[ActionDTO]
    ) -> RCPResult:
        """
        Evaluate policies against actions and return filtered results.
        
        Args:
            ctx: Evaluation context with metrics and metadata
            policies: List of applicable policies
            actions: Actions to evaluate
            
        Returns:
            RCPResult with allowed, modified, blocked actions and metadata
        """
        start_time = time.time()
        
        # If manual override is active, bypass RCP
        if ctx.manual_override_active:
            logger.info(f"Manual override active for {ctx.algo_key}, bypassing RCP")
            return RCPResult(
                allowed=actions,
                notes=["Manual override active - RCP bypassed"]
            )
        
        # Filter applicable policies
        applicable_policies = self._filter_policies(ctx, policies)
        
        if not applicable_policies:
            logger.debug(f"No applicable policies for {ctx.algo_key}")
            return RCPResult(
                allowed=actions,
                notes=["No applicable policies found"]
            )
        
        # Initialize result containers
        allowed_actions = []
        modified_actions = []
        blocked_actions = []
        notes = []
        total_risk_cost = 0.0
        
        # Process each action through the policy pipeline
        for action in actions:
            try:
                result = self._evaluate_action(ctx, applicable_policies, action)
                
                if result["status"] == "allowed":
                    allowed_actions.append(result["action"])
                elif result["status"] == "modified":
                    modified_actions.append(result["action"])
                elif result["status"] == "blocked":
                    blocked_actions.append(result["action"])
                
                notes.extend(result["notes"])
                total_risk_cost += result["risk_cost"]
                
            except Exception as e:
                logger.error(f"Error evaluating action {action.id}: {e}")
                blocked_actions.append(action)
                notes.append(f"Action {action.id} blocked due to evaluation error: {str(e)}")
        
        evaluation_time = (time.time() - start_time) * 1000
        
        return RCPResult(
            allowed=allowed_actions,
            modified=modified_actions,
            blocked=blocked_actions,
            notes=notes,
            risk_cost=total_risk_cost
        )
    
    def _filter_policies(self, ctx: RCPEvaluationContext, policies: List[RCPPolicy]) -> List[RCPPolicy]:
        """Filter policies based on scope, schedule, expiration, and gates."""
        applicable = []
        
        for policy in policies:
            if not policy.enabled:
                continue
            
            # Check expiration
            if policy.expires_at and policy.expires_at < ctx.timestamp:
                continue
            
            # Check scope
            if policy.scope == "algorithm" and policy.algo_key != ctx.algo_key:
                continue
            
            if policy.scope == "segment":
                if not self._matches_segment(ctx, policy.selector):
                    continue
            
            # Check schedule
            if policy.schedule_cron:
                if not self._matches_schedule(policy.schedule_cron, ctx.timestamp):
                    continue
            
            # Check rollout percentage
            if not self._matches_rollout(policy, ctx):
                continue
            
            # Check gates
            if policy.gates and not self._evaluate_gates(ctx, policy.gates):
                continue
            
            applicable.append(policy)
        
        return applicable
    
    def _evaluate_action(
        self, 
        ctx: RCPEvaluationContext, 
        policies: List[RCPPolicy], 
        action: ActionDTO
    ) -> Dict[str, Any]:
        """Evaluate a single action against all applicable policies."""
        
        current_action = action.model_copy(deep=True)
        notes = []
        risk_cost = 0.0
        was_modified = False
        
        for policy in policies:
            try:
                # Apply mutations
                if policy.mutations:
                    mutation_result = self._apply_mutations(current_action, policy.mutations)
                    if mutation_result["modified"]:
                        current_action = mutation_result["action"]
                        was_modified = True
                        notes.extend(mutation_result["notes"])
                
                # Check hard guards
                guard_result = self._check_hard_guards(current_action, policy.hard_guards)
                if guard_result["blocked"]:
                    return {
                        "status": "blocked",
                        "action": current_action,
                        "notes": notes + guard_result["notes"],
                        "risk_cost": risk_cost
                    }
                
                # Check rate limits
                if policy.limits:
                    rate_limit_result = self._check_rate_limits(ctx, policy, current_action)
                    if rate_limit_result["blocked"]:
                        return {
                            "status": "blocked",
                            "action": current_action,
                            "notes": notes + rate_limit_result["notes"],
                            "risk_cost": risk_cost
                        }
                
                # Calculate risk cost
                action_risk = self._calculate_risk_score(current_action)
                risk_cost += action_risk
                
                # Check risk ceiling
                if policy.hard_guards.risk_ceiling_per_tick and risk_cost > policy.hard_guards.risk_ceiling_per_tick:
                    return {
                        "status": "blocked",
                        "action": current_action,
                        "notes": notes + [f"Risk ceiling exceeded: {risk_cost:.3f} > {policy.hard_guards.risk_ceiling_per_tick}"],
                        "risk_cost": risk_cost
                    }
                
                # Monitor mode - log but don't enforce
                if policy.mode == "monitor":
                    notes.append(f"Policy {policy.id} in monitor mode - no enforcement")
                
            except Exception as e:
                logger.error(f"Error applying policy {policy.id} to action {action.id}: {e}")
                notes.append(f"Policy {policy.id} evaluation error: {str(e)}")
        
        status = "modified" if was_modified else "allowed"
        return {
            "status": status,
            "action": current_action,
            "notes": notes,
            "risk_cost": risk_cost
        }
    
    def _matches_segment(self, ctx: RCPEvaluationContext, selector: Optional[Dict[str, Any]]) -> bool:
        """Check if context matches segment selector."""
        if not selector:
            return True
        
        segment_data = ctx.segment_data
        
        # Check geo matching
        if selector.get("geo") and segment_data.get("geo"):
            if segment_data["geo"] not in selector["geo"]:
                return False
        
        # Check device matching
        if selector.get("device") and segment_data.get("device"):
            if segment_data["device"] not in selector["device"]:
                return False
        
        # Check source matching
        if selector.get("source") and segment_data.get("source"):
            if segment_data["source"] not in selector["source"]:
                return False
        
        # Check destination IDs
        if selector.get("destination_ids") and segment_data.get("destination_id"):
            if segment_data["destination_id"] not in selector["destination_ids"]:
                return False
        
        return True
    
    def _matches_schedule(self, cron_expr: str, timestamp: datetime) -> bool:
        """Check if current time matches cron schedule."""
        try:
            cron = croniter(cron_expr, timestamp)
            # Check if we're within a reasonable window of the scheduled time
            next_run = cron.get_next(datetime)
            prev_run = cron.get_prev(datetime)
            
            # Allow 5-minute window around scheduled time
            window_seconds = 300
            time_diff = min(
                abs((timestamp - next_run).total_seconds()),
                abs((timestamp - prev_run).total_seconds())
            )
            
            return time_diff <= window_seconds
        except Exception as e:
            logger.error(f"Error evaluating cron expression {cron_expr}: {e}")
            return True  # Default to allowing if cron parsing fails
    
    def _matches_rollout(self, policy: RCPPolicy, ctx: RCPEvaluationContext) -> bool:
        """Check if action should be included in rollout percentage."""
        if policy.rollout_percent >= 1.0:
            return True
        
        # Use deterministic hash for consistent rollout
        hash_input = f"{policy.id}:{ctx.algo_key}:{ctx.run_id or 'preview'}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        rollout_threshold = int(policy.rollout_percent * 0xFFFFFFFF)
        
        return hash_value <= rollout_threshold
    
    def _evaluate_gates(self, ctx: RCPEvaluationContext, gates: List[GateCondition]) -> bool:
        """Evaluate gate conditions against context metrics."""
        for gate in gates:
            if not self._evaluate_gate_condition(ctx, gate):
                return False
        return True
    
    def _evaluate_gate_condition(self, ctx: RCPEvaluationContext, gate: GateCondition) -> bool:
        """Evaluate a single gate condition."""
        try:
            # Get left value
            left_val = self._get_metric_value(ctx, gate.left)
            if left_val is None:
                logger.warning(f"Gate condition left value not found: {gate.left}")
                return False
            
            # Get right value
            if isinstance(gate.right, str):
                right_val = self._get_metric_value(ctx, gate.right)
                if right_val is None:
                    logger.warning(f"Gate condition right value not found: {gate.right}")
                    return False
            else:
                right_val = gate.right
            
            # Apply factor for ratio operations
            if gate.op in ["ratio_lt", "ratio_gt"] and gate.factor:
                right_val = right_val * gate.factor
            
            # Evaluate condition
            if gate.op == "<" or gate.op == "ratio_lt":
                return left_val < right_val
            elif gate.op == "<=":
                return left_val <= right_val
            elif gate.op == "==":
                return left_val == right_val
            elif gate.op == ">=":
                return left_val >= right_val
            elif gate.op == ">" or gate.op == "ratio_gt":
                return left_val > right_val
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating gate condition: {e}")
            return False
    
    def _get_metric_value(self, ctx: RCPEvaluationContext, metric_path: str) -> Optional[float]:
        """Get metric value from context using dot notation."""
        try:
            parts = metric_path.split(".")
            value = ctx.metrics
            
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            
            return float(value) if value is not None else None
            
        except (ValueError, TypeError):
            return None
    
    def _apply_mutations(self, action: ActionDTO, mutations: List[MutationRule]) -> Dict[str, Any]:
        """Apply mutation rules to an action."""
        modified = False
        notes = []
        
        for mutation in mutations:
            if action.type != mutation.action_type:
                continue
            
            # Check for missing required fields
            if mutation.block_if_missing_fields:
                for field in mutation.block_if_missing_fields:
                    if field not in action.data:
                        notes.append(f"Action blocked: missing required field '{field}'")
                        return {
                            "modified": False,
                            "action": action,
                            "notes": notes,
                            "blocked": True
                        }
            
            # Apply field clamping
            if mutation.clamp_fields:
                for field, limits in mutation.clamp_fields.items():
                    if field in action.data:
                        old_value = action.data[field]
                        new_value = max(limits.get("min", old_value), 
                                      min(limits.get("max", old_value), old_value))
                        if new_value != old_value:
                            action.data[field] = new_value
                            modified = True
                            notes.append(f"Clamped {field}: {old_value} -> {new_value}")
            
            # Apply max delta constraints
            if mutation.max_delta_fields:
                for field, max_delta in mutation.max_delta_fields.items():
                    if field in action.data:
                        old_field = f"old_{field}"
                        if old_field in action.data:
                            old_value = action.data[old_field]
                            new_value = action.data[field]
                            delta = abs(new_value - old_value)
                            
                            if delta > max_delta:
                                # Clamp to max delta
                                if new_value > old_value:
                                    action.data[field] = old_value + max_delta
                                else:
                                    action.data[field] = old_value - max_delta
                                modified = True
                                notes.append(f"Delta clamped {field}: delta {delta:.3f} -> {max_delta}")
        
        return {
            "modified": modified,
            "action": action,
            "notes": notes,
            "blocked": False
        }
    
    def _check_hard_guards(self, action: ActionDTO, guards: GuardLimits) -> Dict[str, Any]:
        """Check action against hard guard limits."""
        notes = []
        
        # Check weight delta
        if guards.weight_delta_max and action.type == "route.update_weight":
            if "weight" in action.data and "old_weight" in action.data:
                delta = abs(action.data["weight"] - action.data["old_weight"])
                if delta > guards.weight_delta_max:
                    return {
                        "blocked": True,
                        "notes": [f"Weight delta {delta:.3f} exceeds limit {guards.weight_delta_max}"]
                    }
        
        # Check budget shift
        if guards.budget_shift_max_percent and "budget" in action.data:
            if "old_budget" in action.data:
                old_budget = action.data["old_budget"]
                new_budget = action.data["budget"]
                if old_budget > 0:
                    shift_percent = abs(new_budget - old_budget) / old_budget
                    if shift_percent > guards.budget_shift_max_percent:
                        return {
                            "blocked": True,
                            "notes": [f"Budget shift {shift_percent:.1%} exceeds limit {guards.budget_shift_max_percent:.1%}"]
                        }
        
        return {"blocked": False, "notes": notes}
    
    def _check_rate_limits(self, ctx: RCPEvaluationContext, policy: RCPPolicy, action: ActionDTO) -> Dict[str, Any]:
        """Check action against rate limits."""
        if not policy.limits:
            return {"blocked": False, "notes": []}
        
        cache_key = f"{policy.id}:{ctx.algo_key}"
        current_time = ctx.timestamp
        window_start = datetime.fromtimestamp(
            current_time.timestamp() - policy.limits.window_seconds
        )
        
        # Clean old entries and count recent actions
        if cache_key not in self.rate_limit_cache:
            self.rate_limit_cache[cache_key] = []
        
        recent_actions = [
            ts for ts in self.rate_limit_cache[cache_key] 
            if ts > window_start
        ]
        
        if len(recent_actions) >= policy.limits.max_actions_in_window:
            return {
                "blocked": True,
                "notes": [f"Rate limit exceeded: {len(recent_actions)} actions in {policy.limits.window_seconds}s window"]
            }
        
        # Add current action to cache
        recent_actions.append(current_time)
        self.rate_limit_cache[cache_key] = recent_actions
        
        return {"blocked": False, "notes": []}
    
    def _calculate_risk_score(self, action: ActionDTO) -> float:
        """Calculate risk score for an action."""
        base_risk = 0.1  # Base risk for any action
        
        # Weight-based risk
        if action.type == "route.update_weight" and "weight" in action.data:
            if "old_weight" in action.data:
                delta = abs(action.data["weight"] - action.data["old_weight"])
                base_risk += delta * 2.0  # Weight changes are risky
        
        # Budget-based risk
        if "budget" in action.data and "old_budget" in action.data:
            old_budget = action.data["old_budget"]
            new_budget = action.data["budget"]
            if old_budget > 0:
                budget_change = abs(new_budget - old_budget) / old_budget
                base_risk += budget_change * 1.5
        
        # Pause actions are high risk
        if action.type in ["destination.pause", "route.pause"]:
            base_risk += 0.5
        
        return min(base_risk, 2.0)  # Cap at 2.0
