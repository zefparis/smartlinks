"""Thompson Sampling bandit implementation."""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from ..observability.otel import trace_function

@dataclass
class BanditArm:
    """Bandit arm with Beta distribution parameters."""
    destination_id: str
    alpha: float = 1.0  # Success count + 1
    beta: float = 1.0   # Failure count + 1
    weight: float = 0.0
    last_updated: Optional[str] = None

class ThompsonBandit:
    """Thompson Sampling bandit for traffic optimization."""
    
    def __init__(self, alpha0: float = 1.0, beta0: float = 1.0, 
                 min_weight: float = 0.01, max_weight: float = 0.8):
        self.alpha0 = alpha0  # Prior alpha
        self.beta0 = beta0    # Prior beta
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.arms: Dict[str, BanditArm] = {}
    
    def add_arm(self, destination_id: str, initial_weight: float = 0.1):
        """Add a new bandit arm."""
        self.arms[destination_id] = BanditArm(
            destination_id=destination_id,
            alpha=self.alpha0,
            beta=self.beta0,
            weight=initial_weight
        )
    
    def update_arm(self, destination_id: str, successes: int, failures: int):
        """Update arm with new observations."""
        if destination_id not in self.arms:
            self.add_arm(destination_id)
        
        arm = self.arms[destination_id]
        arm.alpha += successes
        arm.beta += failures
        arm.last_updated = np.datetime64('now').astype(str)
    
    @trace_function("bandits.thompson.select")
    def select_weights(self, destination_ids: List[str], 
                      total_weight: float = 1.0) -> Dict[str, float]:
        """Select weights using Thompson Sampling."""
        
        # Ensure all destinations have arms
        for dest_id in destination_ids:
            if dest_id not in self.arms:
                self.add_arm(dest_id)
        
        # Sample from Beta distributions
        samples = {}
        for dest_id in destination_ids:
            arm = self.arms[dest_id]
            # Sample from Beta(alpha, beta)
            sample = np.random.beta(arm.alpha, arm.beta)
            samples[dest_id] = sample
        
        # Normalize samples to weights
        total_sample = sum(samples.values())
        if total_sample == 0:
            # Fallback to uniform distribution
            weight_per_dest = total_weight / len(destination_ids)
            return {dest_id: weight_per_dest for dest_id in destination_ids}
        
        weights = {}
        for dest_id in destination_ids:
            raw_weight = (samples[dest_id] / total_sample) * total_weight
            # Apply bounds
            weights[dest_id] = np.clip(raw_weight, self.min_weight, self.max_weight)
        
        # Renormalize to ensure sum equals total_weight
        current_total = sum(weights.values())
        if current_total > 0:
            for dest_id in weights:
                weights[dest_id] = (weights[dest_id] / current_total) * total_weight
        
        return weights
    
    def get_arm_stats(self, destination_id: str) -> Dict[str, float]:
        """Get statistics for an arm."""
        if destination_id not in self.arms:
            return {"alpha": self.alpha0, "beta": self.beta0, "mean": 0.5, "variance": 0.083}
        
        arm = self.arms[destination_id]
        mean = arm.alpha / (arm.alpha + arm.beta)
        variance = (arm.alpha * arm.beta) / ((arm.alpha + arm.beta)**2 * (arm.alpha + arm.beta + 1))
        
        return {
            "alpha": arm.alpha,
            "beta": arm.beta,
            "mean": mean,
            "variance": variance,
            "confidence_95": np.sqrt(variance) * 1.96
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all arms."""
        return {dest_id: self.get_arm_stats(dest_id) for dest_id in self.arms}

class UCBBandit:
    """Upper Confidence Bound bandit implementation."""
    
    def __init__(self, c: float = 1.0, min_weight: float = 0.01, max_weight: float = 0.8):
        self.c = c  # Exploration parameter
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.arms: Dict[str, Dict] = {}
        self.total_rounds = 0
    
    def add_arm(self, destination_id: str, initial_weight: float = 0.1):
        """Add a new bandit arm."""
        self.arms[destination_id] = {
            "total_reward": 0.0,
            "num_pulls": 0,
            "weight": initial_weight
        }
    
    def update_arm(self, destination_id: str, reward: float):
        """Update arm with reward."""
        if destination_id not in self.arms:
            self.add_arm(destination_id)
        
        arm = self.arms[destination_id]
        arm["total_reward"] += reward
        arm["num_pulls"] += 1
        self.total_rounds += 1
    
    @trace_function("bandits.ucb.select")
    def select_weights(self, destination_ids: List[str], 
                      total_weight: float = 1.0) -> Dict[str, float]:
        """Select weights using UCB."""
        
        # Ensure all destinations have arms
        for dest_id in destination_ids:
            if dest_id not in self.arms:
                self.add_arm(dest_id)
        
        # Calculate UCB values
        ucb_values = {}
        for dest_id in destination_ids:
            arm = self.arms[dest_id]
            
            if arm["num_pulls"] == 0:
                # Unplayed arm gets infinite UCB
                ucb_values[dest_id] = float('inf')
            else:
                mean_reward = arm["total_reward"] / arm["num_pulls"]
                confidence = self.c * np.sqrt(np.log(self.total_rounds) / arm["num_pulls"])
                ucb_values[dest_id] = mean_reward + confidence
        
        # Convert UCB values to weights
        if any(v == float('inf') for v in ucb_values.values()):
            # If any arm is unplayed, distribute weight equally among unplayed arms
            unplayed = [dest_id for dest_id, v in ucb_values.items() if v == float('inf')]
            weight_per_unplayed = total_weight / len(unplayed)
            weights = {dest_id: 0.0 for dest_id in destination_ids}
            for dest_id in unplayed:
                weights[dest_id] = weight_per_unplayed
        else:
            # Softmax transformation of UCB values
            exp_values = {dest_id: np.exp(ucb_values[dest_id]) for dest_id in destination_ids}
            total_exp = sum(exp_values.values())
            
            weights = {}
            for dest_id in destination_ids:
                raw_weight = (exp_values[dest_id] / total_exp) * total_weight
                weights[dest_id] = np.clip(raw_weight, self.min_weight, self.max_weight)
            
            # Renormalize
            current_total = sum(weights.values())
            if current_total > 0:
                for dest_id in weights:
                    weights[dest_id] = (weights[dest_id] / current_total) * total_weight
        
        return weights
    
    def get_arm_stats(self, destination_id: str) -> Dict[str, float]:
        """Get statistics for an arm."""
        if destination_id not in self.arms:
            return {"mean_reward": 0.0, "num_pulls": 0, "confidence": 0.0}
        
        arm = self.arms[destination_id]
        mean_reward = arm["total_reward"] / arm["num_pulls"] if arm["num_pulls"] > 0 else 0.0
        confidence = self.c * np.sqrt(np.log(self.total_rounds) / arm["num_pulls"]) if arm["num_pulls"] > 0 else float('inf')
        
        return {
            "mean_reward": mean_reward,
            "num_pulls": arm["num_pulls"],
            "confidence": confidence,
            "ucb_value": mean_reward + confidence
        }

class BanditTrafficOptimizer:
    """Traffic optimizer using bandit algorithms."""
    
    def __init__(self, algorithm: str = "thompson", **kwargs):
        self.algorithm = algorithm
        
        if algorithm == "thompson":
            self.bandit = ThompsonBandit(**kwargs)
        elif algorithm == "ucb":
            self.bandit = UCBBandit(**kwargs)
        else:
            raise ValueError(f"Unknown bandit algorithm: {algorithm}")
    
    @trace_function("bandits.optimize")
    async def optimize_traffic(self, destinations: List[str], 
                              historical_data: Dict[str, Dict], 
                              constraints: Dict[str, float]) -> Dict[str, float]:
        """Optimize traffic allocation using bandits."""
        
        # Update bandit with historical data
        for dest_id, data in historical_data.items():
            if self.algorithm == "thompson":
                successes = data.get("conversions", 0)
                total = data.get("visits", 1)
                failures = max(0, total - successes)
                self.bandit.update_arm(dest_id, successes, failures)
            elif self.algorithm == "ucb":
                reward = data.get("cvr", 0.0)  # Use CVR as reward
                self.bandit.update_arm(dest_id, reward)
        
        # Select new weights
        total_weight = constraints.get("total_weight", 1.0)
        weights = self.bandit.select_weights(destinations, total_weight)
        
        return weights
    
    def get_bandit_stats(self) -> Dict[str, Dict]:
        """Get bandit statistics."""
        if hasattr(self.bandit, 'get_all_stats'):
            return self.bandit.get_all_stats()
        else:
            return {dest_id: self.bandit.get_arm_stats(dest_id) for dest_id in self.bandit.arms}
