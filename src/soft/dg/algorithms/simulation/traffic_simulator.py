"""
Advanced Traffic Simulator for SmartLinks Autonomous DG.

This module simulates realistic traffic patterns for testing and capacity planning.
It can generate synthetic traffic that mimics real-world user behavior.
"""
import logging
import random
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

from ...models.decision import Action, DecisionContext
from ..base import Algorithm, AlgorithmResult

logger = logging.getLogger(__name__)

class TrafficPattern(Enum):
    """Different types of traffic patterns."""
    NORMAL = "normal"
    SPIKE = "spike"
    DIP = "dip"
    WEEKLY = "weekly"
    SEASONAL = "seasonal"
    RANDOM = "random"

class TrafficSimulator(Algorithm):
    """Advanced traffic simulation algorithm."""
    
    # Default configuration
    DEFAULT_CONFIG = {
        "simulation_duration_hours": 24,
        "resolution_minutes": 5,
        "baseline_traffic": 1000,  # Requests per hour
        "patterns": [
            {
                "type": "weekly",
                "weight": 0.6,
                "params": {
                    "weekday_scale": 1.2,
                    "weekend_scale": 0.8,
                    "peak_hours": [9, 12, 14, 18],
                    "peak_scale": 1.5
                }
            },
            {
                "type": "random",
                "weight": 0.2,
                "params": {
                    "min_scale": 0.8,
                    "max_scale": 1.2
                }
            },
            {
                "type": "spike",
                "weight": 0.1,
                "params": {
                    "spike_probability": 0.05,
                    "min_spike_scale": 1.5,
                    "max_spike_scale": 3.0,
                    "duration_minutes": [5, 30]
                }
            }
        ],
        "anomaly_injection": {
            "enabled": True,
            "anomaly_types": [
                {
                    "type": "sudden_spike",
                    "probability": 0.02,
                    "scale": [2.0, 5.0],
                    "duration_minutes": [5, 30]
                },
                {
                    "type": "sudden_drop",
                    "probability": 0.01,
                    "scale": [0.1, 0.5],
                    "duration_minutes": [10, 60]
                }
            ]
        },
        "output_format": "timeseries",
        "random_seed": None
    }
    
    @classmethod
    def get_name(cls) -> str:
        return "traffic_simulator"
    
    def __init__(self):
        self.rng = np.random.RandomState()
        self.simulation_start = None
    
    async def execute(self, context: DecisionContext, 
                     config: Optional[Dict[str, Any]] = None) -> AlgorithmResult:
        """Execute the traffic simulation."""
        config = {**self.DEFAULT_CONFIG, **(config or {})}
        
        try:
            if config.get("random_seed") is not None:
                self.rng = np.random.RandomState(config["random_seed"])
            
            simulation_results = await self._run_simulation(config)
            actions = self._generate_actions(simulation_results, config)
            
            return AlgorithmResult(
                algorithm_name=self.get_name(),
                confidence=0.9,
                recommended_actions=actions,
                data=simulation_results
            )
            
        except Exception as e:
            logger.error(f"Error in traffic simulation: {e}", exc_info=True)
            return AlgorithmResult(
                algorithm_name=self.get_name(),
                confidence=0.0,
                recommended_actions=[],
                metadata={"error": str(e)}
            )
    
    async def _run_simulation(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run the traffic simulation with the given configuration."""
        self.simulation_start = datetime.utcnow()
        duration_minutes = config["simulation_duration_hours"] * 60
        resolution = config["resolution_minutes"]
        time_points = np.arange(0, duration_minutes + resolution, resolution)
        
        # Initialize results
        results = {
            "timestamps": [],
            "request_rates": [],
            "total_requests": 0,
            "anomalies": []
        }
        
        # Generate base traffic pattern
        base_traffic = self._generate_base_traffic(time_points, config)
        
        # Apply anomalies
        traffic_with_anomalies, anomalies = self._inject_anomalies(
            base_traffic, time_points, config
        )
        results["anomalies"] = anomalies
        
        # Convert to request counts per interval
        for i, (timestamp, rate) in enumerate(zip(time_points, traffic_with_anomalies)):
            current_time = self.simulation_start + timedelta(minutes=timestamp)
            requests_this_interval = int(rate * (resolution / 60))
            
            results["total_requests"] += requests_this_interval
            results["timestamps"].append(current_time.isoformat())
            results["request_rates"].append(requests_this_interval)
        
        return results
    
    def _generate_base_traffic(self, time_points: np.ndarray, 
                             config: Dict[str, Any]) -> np.ndarray:
        """Generate base traffic pattern."""
        traffic = np.ones_like(time_points, dtype=float) * config["baseline_traffic"]
        
        for pattern in config["patterns"]:
            pattern_type = pattern["type"]
            weight = pattern["weight"]
            params = pattern.get("params", {})
            
            if pattern_type == "weekly":
                pattern_values = self._weekly_pattern(time_points, params)
            elif pattern_type == "spike":
                pattern_values = self._spike_pattern(time_points, params)
            elif pattern_type == "dip":
                pattern_values = self._dip_pattern(time_points, params)
            else:  # random
                pattern_values = self._random_pattern(time_points, params)
            
            traffic = traffic * (1 - weight) + traffic * pattern_values * weight
        
        return traffic
    
    def _weekly_pattern(self, time_points: np.ndarray, 
                       params: Dict[str, Any]) -> np.ndarray:
        """Generate weekly traffic pattern."""
        pattern = np.ones_like(time_points, dtype=float)
        
        for i, t in enumerate(time_points):
            dt = self.simulation_start + timedelta(minutes=t)
            hour = dt.hour
            
            # Weekday/weekend pattern
            if dt.weekday() < 5:  # Weekday
                pattern[i] *= params.get("weekday_scale", 1.2)
            else:  # Weekend
                pattern[i] *= params.get("weekend_scale", 0.8)
            
            # Peak hours
            if hour in params.get("peak_hours", []):
                pattern[i] *= params.get("peak_scale", 1.5)
        
        return pattern
    
    def _spike_pattern(self, time_points: np.ndarray, 
                      params: Dict[str, Any]) -> np.ndarray:
        """Generate random traffic spikes."""
        pattern = np.ones_like(time_points, dtype=float)
        spike_prob = params.get("spike_probability", 0.05)
        min_scale = params.get("min_spike_scale", 1.5)
        max_scale = params.get("max_spike_scale", 3.0)
        min_dur, max_dur = params.get("duration_minutes", [5, 30])
        
        i = 0
        while i < len(time_points):
            if self.rng.random() < spike_prob / (len(time_points) / 1000):
                duration = self.rng.randint(min_dur, max_dur + 1)
                scale = self.rng.uniform(min_scale, max_scale)
                
                for j in range(i, min(i + duration, len(time_points))):
                    pattern[j] = scale
                
                i += duration
            else:
                i += 1
        
        return pattern
    
    def _dip_pattern(self, time_points: np.ndarray, 
                    params: Dict[str, Any]) -> np.ndarray:
        """Generate random traffic dips."""
        pattern = np.ones_like(time_points, dtype=float)
        dip_prob = params.get("dip_probability", 0.03)
        min_scale = params.get("min_dip_scale", 0.3)
        max_scale = params.get("max_dip_scale", 0.7)
        min_dur, max_dur = params.get("duration_minutes", [10, 60])
        
        i = 0
        while i < len(time_points):
            if self.rng.random() < dip_prob / (len(time_points) / 1000):
                duration = self.rng.randint(min_dur, max_dur + 1)
                scale = self.rng.uniform(min_scale, max_scale)
                
                for j in range(i, min(i + duration, len(time_points))):
                    pattern[j] = scale
                
                i += duration
            else:
                i += 1
        
        return pattern
    
    def _random_pattern(self, time_points: np.ndarray, 
                       params: Dict[str, Any]) -> np.ndarray:
        """Generate random traffic pattern."""
        min_scale = params.get("min_scale", 0.8)
        max_scale = params.get("max_scale", 1.2)
        return self.rng.uniform(min_scale, max_scale, size=len(time_points))
    
    def _inject_anomalies(self, base_traffic: np.ndarray, 
                         time_points: np.ndarray,
                         config: Dict[str, Any]) -> Tuple[np.ndarray, List[Dict]]:
        """Inject anomalies into the traffic pattern."""
        if not config["anomaly_injection"]["enabled"]:
            return base_traffic, []
        
        traffic = base_traffic.copy()
        anomalies = []
        
        for anomaly_type in config["anomaly_injection"]["anomaly_types"]:
            if self.rng.random() < anomaly_type["probability"]:
                if anomaly_type["type"] == "sudden_spike":
                    traffic, anomaly = self._inject_sudden_spike(
                        traffic, time_points, anomaly_type
                    )
                elif anomaly_type["type"] == "sudden_drop":
                    traffic, anomaly = self._inject_sudden_drop(
                        traffic, time_points, anomaly_type
                    )
                else:
                    continue
                
                if anomaly:
                    anomalies.append(anomaly)
        
        return traffic, anomalies
    
    def _inject_sudden_spike(self, traffic: np.ndarray, 
                           time_points: np.ndarray,
                           params: Dict[str, Any]) -> Tuple[np.ndarray, Dict]:
        """Inject a sudden traffic spike."""
        min_scale, max_scale = params.get("scale", [2.0, 5.0])
        min_dur, max_dur = params.get("duration_minutes", [5, 30])
        
        scale = self.rng.uniform(min_scale, max_scale)
        duration = self.rng.randint(min_dur, max_dur + 1)
        
        if len(time_points) <= duration:
            return traffic, None
            
        start_idx = self.rng.randint(0, len(time_points) - duration)
        traffic[start_idx:start_idx + duration] *= scale
        
        anomaly = {
            "type": "sudden_spike",
            "start_time": (self.simulation_start + timedelta(minutes=time_points[start_idx])).isoformat(),
            "duration_minutes": duration,
            "scale": scale,
            "impact": "increased traffic"
        }
        
        return traffic, anomaly
    
    def _inject_sudden_drop(self, traffic: np.ndarray, 
                          time_points: np.ndarray,
                          params: Dict[str, Any]) -> Tuple[np.ndarray, Dict]:
        """Inject a sudden traffic drop."""
        min_scale, max_scale = params.get("scale", [0.1, 0.5])
        min_dur, max_dur = params.get("duration_minutes", [10, 60])
        
        scale = self.rng.uniform(min_scale, max_scale)
        duration = self.rng.randint(min_dur, max_dur + 1)
        
        if len(time_points) <= duration:
            return traffic, None
            
        start_idx = self.rng.randint(0, len(time_points) - duration)
        traffic[start_idx:start_idx + duration] *= scale
        
        anomaly = {
            "type": "sudden_drop",
            "start_time": (self.simulation_start + timedelta(minutes=time_points[start_idx])).isoformat(),
            "duration_minutes": duration,
            "scale": scale,
            "impact": "decreased traffic"
        }
        
        return traffic, anomaly
    
    def _generate_actions(self, simulation_results: Dict[str, Any],
                         config: Dict[str, Any]) -> List[Action]:
        """Generate recommended actions based on simulation results."""
        actions = []
        
        for anomaly in simulation_results.get("anomalies", []):
            if anomaly["type"] == "sudden_spike":
                actions.append(Action(
                    action_type="scale_resources",
                    params={
                        "direction": "up",
                        "reason": f"Traffic spike detected: {anomaly['scale']:.1f}x",
                        "start_time": anomaly["start_time"],
                        "duration_minutes": anomaly["duration_minutes"]
                    },
                    priority=80,
                    description="Scale up resources for traffic spike",
                    source_algorithm=self.get_name()
                ))
            elif anomaly["type"] == "sudden_drop":
                actions.append(Action(
                    action_type="investigate_issue",
                    params={
                        "issue_type": "traffic_drop",
                        "severity": "high",
                        "start_time": anomaly["start_time"],
                        "duration_minutes": anomaly["duration_minutes"]
                    },
                    priority=90,
                    description="Investigate traffic drop",
                    source_algorithm=self.get_name()
                ))
        
        return actions
