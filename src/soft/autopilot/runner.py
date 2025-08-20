"""Algorithm runner that loads settings and applies AI policies."""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, sessionmaker

from .models import AlgorithmSettings, AIPolicy, AuditSettings, AuthorityLevel, AlgorithmRun
from .schemas import ALGORITHM_SETTINGS_MAP
from ..dg.dependencies import get_db
from ..rcp.repository import RCPRepository
from ..rcp.evaluator import RCPEvaluator
from ..rcp.schemas import (
    RCPEvaluationContext, ActionDTO, RCPPolicy, 
    RCPEvaluationStats, RCPEvaluationDiff
)

logger = logging.getLogger(__name__)


class AlgorithmRunner:
    """Manages algorithm execution with settings and AI governance."""
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.running_algorithms = {}
        self.risk_budgets = {}  # Track daily risk usage
        self.rcp_evaluator = RCPEvaluator()
        
    async def load_algorithm_settings(self, algo_key: str) -> Dict[str, Any]:
        """Load algorithm settings from database with defaults."""
        with self.db_session_factory() as db:
            settings_record = db.query(AlgorithmSettings).filter(
                AlgorithmSettings.algo_key == algo_key
            ).first()
            
            if settings_record:
                return settings_record.settings_json
            else:
                # Return defaults
                settings_class = ALGORITHM_SETTINGS_MAP.get(algo_key)
                if settings_class:
                    default_settings = settings_class()
                    return default_settings.dict()
                return {}
    
    async def load_ai_policy(self, algo_key: str) -> Dict[str, Any]:
        """Load AI policy for algorithm."""
        with self.db_session_factory() as db:
            policy_record = db.query(AIPolicy).filter(
                AIPolicy.algo_key == algo_key
            ).first()
            
            if policy_record:
                return {
                    "authority": policy_record.authority,
                    "risk_budget_daily": policy_record.risk_budget_daily,
                    "dry_run": policy_record.dry_run,
                    "hard_guards": policy_record.hard_guards_json,
                    "soft_guards": policy_record.soft_guards_json
                }
            else:
                # Return defaults
                return {
                    "authority": AuthorityLevel.SAFE_APPLY,
                    "risk_budget_daily": 3,
                    "dry_run": False,
                    "hard_guards": {},
                    "soft_guards": {}
                }
    
    async def check_risk_budget(self, algo_key: str, action_risk: float) -> bool:
        """Check if action is within daily risk budget."""
        today = datetime.now().date()
        budget_key = f"{algo_key}_{today}"
        
        # Get policy
        policy = await self.load_ai_policy(algo_key)
        daily_limit = policy["risk_budget_daily"]
        
        # Track current usage
        current_usage = self.risk_budgets.get(budget_key, 0.0)
        
        if current_usage + action_risk > daily_limit:
            logger.warning(f"Risk budget exceeded for {algo_key}: {current_usage + action_risk} > {daily_limit}")
            return False
        
        return True
    
    async def apply_hard_guards(self, algo_key: str, action: Dict[str, Any]) -> bool:
        """Apply hard guards to validate action."""
        policy = await self.load_ai_policy(algo_key)
        hard_guards = policy.get("hard_guards", {})
        
        # Example hard guard checks
        if "weight_delta_max" in hard_guards:
            if action.get("type") == "reweight":
                delta = abs(action.get("new_value", 0) - action.get("current_value", 0))
                if delta > hard_guards["weight_delta_max"]:
                    logger.warning(f"Hard guard violation: weight delta {delta} > {hard_guards['weight_delta_max']}")
                    return False
        
        if "budget_shift_max_percent" in hard_guards:
            if action.get("type") == "budget_shift":
                current = action.get("current_value", 0)
                new = action.get("new_value", 0)
                if current > 0:
                    percent_change = abs(new - current) / current
                    if percent_change > hard_guards["budget_shift_max_percent"]:
                        logger.warning(f"Hard guard violation: budget shift {percent_change} > {hard_guards['budget_shift_max_percent']}")
                        return False
        
        return True
    
    async def execute_action(self, algo_key: str, action: Dict[str, Any]) -> bool:
        """Execute algorithm action with governance checks."""
        try:
            # Load policy
            policy = await self.load_ai_policy(algo_key)
            
            # Check authority level
            if policy["authority"] == AuthorityLevel.ADVISORY:
                logger.info(f"Advisory mode: would execute {action}")
                return True
            
            # Check dry run mode
            if policy["dry_run"]:
                logger.info(f"Dry run mode: would execute {action}")
                return True
            
            # Check risk budget
            action_risk = action.get("risk_score", 0.0)
            if not await self.check_risk_budget(algo_key, action_risk):
                return False
            
            # Apply hard guards
            if not await self.apply_hard_guards(algo_key, action):
                return False
            
            # Execute the actual action
            success = await self._execute_algorithm_action(algo_key, action)
            
            if success:
                # Update risk budget usage
                today = datetime.now().date()
                budget_key = f"{algo_key}_{today}"
                self.risk_budgets[budget_key] = self.risk_budgets.get(budget_key, 0.0) + action_risk
                
                # Log audit trail
                await self._log_action_audit(algo_key, action, "executed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error executing action for {algo_key}: {e}")
            await self._log_action_audit(algo_key, action, "error", str(e))
            return False
    
    async def _execute_algorithm_action(self, algo_key: str, action: Dict[str, Any]) -> bool:
        """Execute the actual algorithm action (implement algorithm-specific logic)."""
        action_type = action.get("type")
        
        if action_type == "reweight":
            # Implement traffic reweighting logic
            logger.info(f"Reweighting {action.get('target')} from {action.get('current_value')} to {action.get('new_value')}")
            return True
            
        elif action_type == "budget_shift":
            # Implement budget reallocation logic
            logger.info(f"Shifting budget for {action.get('target')} from {action.get('current_value')} to {action.get('new_value')}")
            return True
            
        elif action_type == "pause_destination":
            # Implement destination pausing logic
            logger.info(f"Pausing destination {action.get('target')}")
            return True
            
        else:
            logger.warning(f"Unknown action type: {action_type}")
            return False
    
    async def _log_action_audit(self, algo_key: str, action: Dict[str, Any], status: str, error: Optional[str] = None):
        """Log action to audit trail."""
        with self.db_session_factory() as db:
            audit_entry = AuditSettings(
                algo_key=algo_key,
                actor="algorithm_runner",
                diff_json={
                    "action": action,
                    "status": status,
                    "error": error,
                    "timestamp": datetime.now().isoformat()
                },
                created_at=datetime.now()
            )
            db.add(audit_entry)
            db.commit()
    
    async def run_algorithm(self, algo_key: str, manual_override: bool = False) -> Dict[str, Any]:
        """Run algorithm with loaded settings and governance."""
        run_id = str(uuid.uuid4())
        
        try:
            # Create algorithm run record
            await self._create_algorithm_run(run_id, algo_key)
            
            # Load settings and policy
            settings = await self.load_algorithm_settings(algo_key)
            policy = await self.load_ai_policy(algo_key)
            
            # Check if algorithm is active
            if not settings.get("active", False):
                await self._update_algorithm_run(
                    run_id=run_id,
                    algo_key=algo_key,
                    settings_version=settings.get("version", 1),
                    ai_authority_used=policy.get("authority_level", "advisory"),
                    risk_cost=0.0,
                    rcp_applied=False,
                    status="inactive",
                    error_message="Algorithm is disabled"
                )
                return {"status": "inactive", "message": "Algorithm is disabled"}
            
            # Generate algorithm actions (mock implementation)
            raw_actions = await self._generate_algorithm_actions(algo_key, settings)
            
            # Convert to ActionDTO format for RCP evaluation
            action_dtos = []
            for action in raw_actions:
                action_dto = ActionDTO(
                    id=str(uuid.uuid4()),
                    type=action.get("type", "unknown"),
                    algo_key=algo_key,
                    idempotency_key=action.get("idempotency_key", str(uuid.uuid4())),
                    data=action,
                    risk_score=action.get("risk_score", 0.0)
                )
                action_dtos.append(action_dto)
            
            # Apply RCP evaluation before execution
            final_actions = action_dtos
            rcp_applied = False
            total_risk_cost = 0.0
            
            if not manual_override:
                rcp_result = await self._apply_rcp_policies(algo_key, action_dtos, run_id)
                if rcp_result:
                    final_actions = rcp_result.allowed + rcp_result.modified
                    total_risk_cost = rcp_result.risk_cost
                    rcp_applied = True
                    
                    # Log blocked actions
                    if rcp_result.blocked:
                        logger.info(f"RCP blocked {len(rcp_result.blocked)} actions for {algo_key}")
                        for blocked_action in rcp_result.blocked:
                            await self.audit_action(algo_key, blocked_action.data, "blocked_by_rcp")
            
            # Execute final actions
            executed_actions = []
            failed_actions = []
            
            for action_dto in final_actions:
                success = await self.execute_action(algo_key, action_dto.data)
                if success:
                    executed_actions.append(action_dto.data)
                else:
                    failed_actions.append(action_dto.data)
            
            # Update algorithm run record with RCP info
            await self._update_algorithm_run(
                run_id=run_id,
                algo_key=algo_key,
                settings_version=settings.get("version", 1),
                ai_authority_used=policy.get("authority_level", "advisory"),
                risk_cost=total_risk_cost,
                rcp_applied=rcp_applied
            )
            
            return {
                "status": "completed",
                "run_id": run_id,
                "executed_actions": len(executed_actions),
                "failed_actions": len(failed_actions),
                "total_risk_used": sum(a.get("risk_score", 0) for a in executed_actions),
                "rcp_applied": rcp_applied,
                "rcp_risk_cost": total_risk_cost
            }
            
        except Exception as e:
            logger.error(f"Error running algorithm {algo_key}: {e}")
            return {"status": "error", "message": str(e), "run_id": run_id}
    
    async def _apply_rcp_policies(self, algo_key: str, actions: List[ActionDTO], run_id: str) -> Optional[Any]:
        """Apply RCP policies to algorithm actions."""
        try:
            with self.db_session_factory() as db:
                rcp_repo = RCPRepository(db)
                
                # Get applicable policies
                policies = rcp_repo.get_applicable_policies(algo_key)
                if not policies:
                    return None
                
                # Convert to Pydantic models
                policy_schemas = [RCPPolicy.from_orm(p) for p in policies]
                
                # Create evaluation context
                ctx = RCPEvaluationContext(
                    algo_key=algo_key,
                    run_id=run_id,
                    metrics=await self._get_current_metrics(algo_key),
                    segment_data=await self._get_segment_data(algo_key),
                    manual_override_active=False
                )
                
                # Evaluate policies
                result = self.rcp_evaluator.evaluate_policies(ctx, policy_schemas, actions)
                
                # Persist evaluation records
                for policy in policies:
                    stats = RCPEvaluationStats(
                        risk_cost=result.risk_cost,
                        actions_allowed=len(result.allowed),
                        actions_modified=len(result.modified),
                        actions_blocked=len(result.blocked),
                        evaluation_time_ms=0.0,  # Would be measured in real implementation
                        policies_applied=len(policy_schemas)
                    )
                    
                    diff = RCPEvaluationDiff(
                        before=actions,
                        after=result.allowed + result.modified,
                        changes=result.notes
                    )
                    
                    # Determine result type
                    if result.blocked and (result.allowed or result.modified):
                        result_type = "mixed"
                    elif result.blocked:
                        result_type = "blocked"
                    elif result.modified:
                        result_type = "modified"
                    else:
                        result_type = "allowed"
                    
                    rcp_repo.create_evaluation(
                        policy_id=policy.id,
                        algo_key=algo_key,
                        run_id=run_id,
                        result=result_type,
                        stats=stats,
                        diff=diff
                    )
                
                return result
                
        except Exception as e:
            logger.error(f"Error applying RCP policies for {algo_key}: {e}")
            return None
    
    async def _get_current_metrics(self, algo_key: str) -> Dict[str, float]:
        """Get current metrics for RCP evaluation."""
        # Mock implementation - would fetch real metrics
        return {
            "cvr_1h": 0.05,
            "cvr_24h_mean": 0.048,
            "traffic_volume": 1000.0,
            "error_rate": 0.01
        }
    
    async def _get_segment_data(self, algo_key: str) -> Dict[str, Any]:
        """Get segment data for RCP evaluation."""
        # Mock implementation - would fetch real segment data
        return {
            "geo": "US",
            "device": "mobile",
            "source": "organic"
        }
    
    async def _generate_algorithm_actions(self, algo_key: str, settings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate algorithm actions based on settings (mock implementation)."""
        # This would contain the actual algorithm logic
        # For now, return mock actions
        
        if algo_key == "traffic_optimizer":
            return [
                {
                    "type": "reweight",
                    "target": "destination_123",
                    "current_value": 0.25,
                    "new_value": 0.30,
                    "risk_score": 0.2,
                    "justification": "CVR improvement detected"
                }
            ]
        
        elif algo_key == "budget_arbitrage":
            return [
                {
                    "type": "budget_shift",
                    "target": "campaign_456",
                    "current_value": 1000.0,
                    "new_value": 1200.0,
                    "risk_score": 0.3,
                    "justification": "ROI above target"
                }
            ]
        
        return []


# Global runner instance
runner = None

def get_runner():
    """Get global runner instance."""
    global runner
    if runner is None:
        # Initialize with database session factory
        from ..dg.dependencies import get_db_session_factory
        runner = AlgorithmRunner(get_db_session_factory())
    return runner
