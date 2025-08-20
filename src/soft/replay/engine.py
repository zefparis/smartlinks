"""Decision Graph & Replay engine."""

import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..pac.schemas import DecisionNode, DecisionEdge, DecisionGraph, ReplayRequest, WhatIfRequest
# from ..rcp.evaluator import RCPEvaluator  # Comment out if module doesn't exist
# from ..rcp.schemas import ActionDTO, RCPResult  # Comment out if module doesn't exist
from ..features.service import FeatureService

@dataclass
class ReplayContext:
    """Replay execution context."""
    timestamp: datetime
    algo_key: str
    metrics: Dict[str, Any]
    features: Dict[str, Any]
    overrides: Dict[str, Any] = None

class DecisionGraphBuilder:
    """Builds decision graphs for RCP evaluation."""
    
    def __init__(self, feature_service: FeatureService):
        self.feature_service = feature_service
        self.nodes = []
        self.edges = []
        self.node_counter = 0
    
    def reset(self):
        """Reset builder state."""
        self.nodes = []
        self.edges = []
        self.node_counter = 0
    
    def add_node(self, node_type: str, label: str, value: Any = None, 
                 status: str = None, metadata: Dict[str, Any] = None) -> str:
        """Add node to graph."""
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1
        
        node = DecisionNode(
            id=node_id,
            type=node_type,
            label=label,
            value=value,
            status=status,
            metadata=metadata or {}
        )
        
        self.nodes.append(node)
        return node_id
    
    def add_edge(self, from_node: str, to_node: str, label: str = None, condition: str = None):
        """Add edge to graph."""
        edge = DecisionEdge(
            from_node=from_node,
            to_node=to_node,
            label=label,
            condition=condition
        )
        self.edges.append(edge)
    
    def build_graph(self, run_id: str, algo_key: str, context: Dict[str, Any], 
                   result: Dict[str, Any]) -> DecisionGraph:
        """Build complete decision graph."""
        return DecisionGraph(
            run_id=run_id,
            algo_key=algo_key,
            timestamp=datetime.utcnow(),
            nodes=self.nodes,
            edges=self.edges,
            context=context,
            final_result=result
        )

class ReplayEngine:
    """Replay engine for decision debugging."""
    
    def __init__(self, rcp_evaluator: RCPEvaluator, feature_service: FeatureService):
        self.rcp_evaluator = rcp_evaluator
        self.feature_service = feature_service
        self.graph_builder = DecisionGraphBuilder(feature_service)
    
    async def replay_decision(self, request: ReplayRequest) -> DecisionGraph:
        """Replay a decision at a specific timestamp."""
        
        # Build replay context
        context = await self._build_replay_context(request)
        
        # Get actions (from request or reconstruct)
        actions = request.actions or await self._reconstruct_actions(request, context)
        
        # Reset graph builder
        self.graph_builder.reset()
        
        # Replay RCP evaluation with graph tracking
        result = await self._replay_rcp_evaluation(actions, context)
        
        # Build final graph
        run_id = f"replay_{request.timestamp.strftime('%Y%m%d_%H%M%S')}"
        graph = self.graph_builder.build_graph(
            run_id=run_id,
            algo_key=request.algo_key,
            context=context.__dict__,
            final_result=result.dict()
        )
        
        return graph
    
    async def _build_replay_context(self, request: ReplayRequest) -> ReplayContext:
        """Build context for replay."""
        
        # Get historical features
        features = await self.feature_service.get_features_at_time(
            timestamp=request.timestamp,
            horizon_minutes=request.horizon_minutes
        )
        
        # Get historical metrics
        metrics = await self._get_historical_metrics(
            request.algo_key,
            request.timestamp,
            request.horizon_minutes
        )
        
        return ReplayContext(
            timestamp=request.timestamp,
            algo_key=request.algo_key,
            metrics=metrics,
            features=features,
            overrides=request.context_override or {}
        )
    
    async def _reconstruct_actions(self, request: ReplayRequest, context: ReplayContext) -> List[Dict]:
        """Reconstruct actions that would have been generated."""
        # This would call the actual algorithm with historical context
        # For now, return mock actions
        return [
            {
                "action_type": "route.update_weight",
                "target_id": "dest_123",
                "parameters": {"weight": 0.3, "old_weight": 0.2},
                "algorithm_id": request.algo_key,
                "segment_id": "mobile"
            }
        ]
    
    async def _replay_rcp_evaluation(self, actions: List[Dict], context: ReplayContext) -> Dict:
        """Replay RCP evaluation with graph tracking."""
        
        # Add context node
        ctx_node = self.graph_builder.add_node(
            "metric", "Context", 
            value={"timestamp": context.timestamp.isoformat(), "algo": context.algo_key},
            status="pass"
        )
        
        # Add input actions node
        actions_node = self.graph_builder.add_node(
            "action", f"Input Actions ({len(actions)})",
            value=actions,
            status="pass"
        )
        
        self.graph_builder.add_edge(ctx_node, actions_node, "generates")
        
        # Mock RCP evaluation with graph tracking
        # In real implementation, this would call the actual RCP evaluator
        # with instrumentation to build the graph
        
        # Add policy nodes
        policy_node = self.graph_builder.add_node(
            "gate", "Policy Filter",
            value={"policies_found": 2, "applicable": 1},
            status="pass"
        )
        
        self.graph_builder.add_edge(actions_node, policy_node, "evaluates")
        
        # Add gate evaluation
        gate_node = self.graph_builder.add_node(
            "gate", "Time Gate",
            value={"current_hour": context.timestamp.hour, "allowed_hours": "9-17"},
            status="pass" if 9 <= context.timestamp.hour <= 17 else "fail"
        )
        
        self.graph_builder.add_edge(policy_node, gate_node, "checks")
        
        # Add guard evaluation
        guard_node = self.graph_builder.add_node(
            "guard", "Weight Delta Guard",
            value={"max_delta": 0.15, "actual_delta": 0.1},
            status="pass"
        )
        
        self.graph_builder.add_edge(gate_node, guard_node, "validates")
        
        # Add mutation
        mutation_node = self.graph_builder.add_node(
            "mutation", "Weight Clamp",
            value={"min": 0.01, "max": 0.8, "applied": True},
            status="pass"
        )
        
        self.graph_builder.add_edge(guard_node, mutation_node, "applies")
        
        # Add result
        result_node = self.graph_builder.add_node(
            "result", "Final Result",
            value={"allowed": len(actions), "modified": 0, "blocked": 0},
            status="pass"
        )
        
        self.graph_builder.add_edge(mutation_node, result_node, "produces")
        
        # Return mock result
        return {
            "allowed": actions[:2],  # Allow first 2 actions
            "modified": [],
            "blocked": actions[2:],  # Block remaining actions
            "risk_cost": 25.5
        }
    
    async def _get_historical_metrics(self, algo_key: str, timestamp: datetime, 
                                    horizon_minutes: int) -> Dict[str, Any]:
        """Get historical metrics for replay."""
        # Mock historical metrics
        return {
            "cvr_1h": 0.025,
            "cvr_24h_mean": 0.028,
            "volume_1h": 1000,
            "revenue_1h": 2500.0
        }

class WhatIfSimulator:
    """What-if simulation engine."""
    
    def __init__(self, rcp_evaluator: RCPEvaluator, feature_service: FeatureService):
        self.rcp_evaluator = rcp_evaluator
        self.feature_service = feature_service
    
    async def simulate(self, request: WhatIfRequest) -> Dict[str, Any]:
        """Run what-if simulation with sliders."""
        
        # Apply slider adjustments to base context
        adjusted_context = self._apply_sliders(request.base_context, request.sliders)
        
        # Generate actions based on adjusted context
        actions = await self._generate_actions_for_context(request.algo_key, adjusted_context)
        
        # Evaluate with RCP
        result = await self.rcp_evaluator.evaluate_action_list(actions, adjusted_context)
        
        # Calculate impact metrics
        impact = self._calculate_impact(request.base_context, adjusted_context, result)
        
        return {
            "adjusted_context": adjusted_context,
            "generated_actions": [action.dict() for action in actions],
            "rcp_result": result.dict(),
            "impact_metrics": impact,
            "simulation_id": self._generate_simulation_id(request)
        }
    
    def _apply_sliders(self, base_context: Dict[str, Any], sliders: Dict[str, float]) -> Dict[str, Any]:
        """Apply slider adjustments to context."""
        adjusted = base_context.copy()
        
        for slider_key, multiplier in sliders.items():
            if slider_key == "volume_multiplier":
                adjusted["volume"] = adjusted.get("volume", 1000) * multiplier
            elif slider_key == "cvr_adjustment":
                adjusted["cvr"] = adjusted.get("cvr", 0.025) + multiplier
            elif slider_key == "budget_multiplier":
                adjusted["budget"] = adjusted.get("budget", 10000) * multiplier
        
        return adjusted
    
    async def _generate_actions_for_context(self, algo_key: str, context: Dict[str, Any]) -> List[ActionDTO]:
        """Generate actions for given context."""
        # Mock action generation based on context
        volume = context.get("volume", 1000)
        cvr = context.get("cvr", 0.025)
        
        # Simple logic: higher volume -> more aggressive weight changes
        weight_delta = min(0.15, volume / 10000)
        
        return [
            ActionDTO(
                action_type="route.update_weight",
                target_id=f"dest_{i}",
                parameters={
                    "weight": 0.2 + weight_delta,
                    "old_weight": 0.2,
                    "expected_cvr": cvr
                },
                algorithm_id=algo_key,
                segment_id="mobile"
            )
            for i in range(min(5, int(volume / 200)))  # Scale actions with volume
        ]
    
    def _calculate_impact(self, base_context: Dict[str, Any], adjusted_context: Dict[str, Any], 
                         result: RCPResult) -> Dict[str, Any]:
        """Calculate impact metrics."""
        base_volume = base_context.get("volume", 1000)
        adj_volume = adjusted_context.get("volume", 1000)
        
        base_cvr = base_context.get("cvr", 0.025)
        adj_cvr = adjusted_context.get("cvr", 0.025)
        
        return {
            "volume_change_pct": ((adj_volume - base_volume) / base_volume) * 100,
            "cvr_change_pct": ((adj_cvr - base_cvr) / base_cvr) * 100,
            "actions_allowed": len(result.allowed),
            "actions_blocked": len(result.blocked),
            "estimated_revenue_impact": (adj_volume * adj_cvr - base_volume * base_cvr) * 100,  # $100 per conversion
            "risk_score": result.risk_cost
        }
    
    def _generate_simulation_id(self, request: WhatIfRequest) -> str:
        """Generate unique simulation ID."""
        content = f"{request.algo_key}_{request.sliders}_{datetime.utcnow().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

class ShadowRunner:
    """Shadow run execution engine."""
    
    def __init__(self, rcp_evaluator: RCPEvaluator):
        self.rcp_evaluator = rcp_evaluator
        self.active_shadows = {}
    
    async def enable_shadow(self, algo_key: str, duration_minutes: Optional[int] = None, 
                          sample_rate: float = 1.0):
        """Enable shadow mode for algorithm."""
        self.active_shadows[algo_key] = {
            "enabled": True,
            "start_time": datetime.utcnow(),
            "duration_minutes": duration_minutes,
            "sample_rate": sample_rate,
            "runs": []
        }
    
    async def disable_shadow(self, algo_key: str):
        """Disable shadow mode."""
        if algo_key in self.active_shadows:
            self.active_shadows[algo_key]["enabled"] = False
    
    async def execute_shadow_run(self, algo_key: str, actions: List[ActionDTO], 
                                context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute shadow run if enabled."""
        shadow_config = self.active_shadows.get(algo_key)
        if not shadow_config or not shadow_config["enabled"]:
            return None
        
        # Check duration
        if shadow_config["duration_minutes"]:
            elapsed = datetime.utcnow() - shadow_config["start_time"]
            if elapsed.total_seconds() > shadow_config["duration_minutes"] * 60:
                await self.disable_shadow(algo_key)
                return None
        
        # Sample rate check
        import random
        if random.random() > shadow_config["sample_rate"]:
            return None
        
        # Execute shadow evaluation
        result = await self.rcp_evaluator.evaluate_action_list(actions, context)
        
        # Log shadow run
        shadow_run = {
            "timestamp": datetime.utcnow().isoformat(),
            "actions_count": len(actions),
            "result": result.dict(),
            "context_hash": hashlib.md5(json.dumps(context, sort_keys=True).encode()).hexdigest()
        }
        
        shadow_config["runs"].append(shadow_run)
        
        return shadow_run
    
    def get_shadow_status(self, algo_key: str) -> Dict[str, Any]:
        """Get shadow run status."""
        shadow_config = self.active_shadows.get(algo_key)
        if not shadow_config:
            return {"enabled": False}
        
        return {
            "enabled": shadow_config["enabled"],
            "start_time": shadow_config["start_time"].isoformat(),
            "duration_minutes": shadow_config["duration_minutes"],
            "sample_rate": shadow_config["sample_rate"],
            "runs_count": len(shadow_config["runs"]),
            "last_run": shadow_config["runs"][-1] if shadow_config["runs"] else None
        }
