"""
Script to initialize default RCP (Runtime Control Policies) for production environment.
"""

import sys
import os
import uuid
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backend.database import get_db
from src.soft.rcp.models import RCPPolicy, RCPScope, RCPMode, RCPAuthority

def create_default_policies():
    """Create default RCP policies for all algorithms."""
    db = next(get_db())
    
    # Default policies for algorithms
    default_policies = [
        {
            "id": str(uuid.uuid4()),
            "name": "Traffic Optimizer - Production Policy",
            "scope": RCPScope.ALGORITHM,
            "algo_key": "traffic_optimizer",
            "mode": RCPMode.ENFORCE,
            "authority_required": RCPAuthority.DG_AI,
            "hard_guards_json": {
                "max_traffic_shift": 0.3,  # Maximum 30% traffic shift per adjustment
                "min_traffic_per_offer": 0.01  # Minimum 1% traffic per offer
            },
            "soft_guards_json": {
                "exploration_rate": 0.05  # 5% exploration rate
            },
            "limits_json": {
                "optimization_interval_hours": 1  # Optimize every hour
            },
            "gates_json": {
                "min_data_threshold": 50  # Require at least 50 conversions for optimization
            },
            "rollout_percent": 1.0,
            "enabled": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Budget Arbitrage - Production Policy",
            "scope": RCPScope.ALGORITHM,
            "algo_key": "budget_arbitrage",
            "mode": RCPMode.ENFORCE,
            "authority_required": RCPAuthority.DG_AI,
            "hard_guards_json": {
                "max_daily_change_pct": 15,  # Maximum 15% budget change per day
                "min_budget": 10.0  # Minimum $10 budget
            },
            "soft_guards_json": {
                "learning_rate": 0.05  # Conservative learning rate
            },
            "limits_json": {
                "lookback_days": 7  # Use 7 days of historical data
            },
            "gates_json": {
                "min_roi_threshold": 1.2  # Minimum 1.2x ROI to consider viable
            },
            "rollout_percent": 1.0,
            "enabled": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Thompson Sampling Bandit - Production Policy",
            "scope": RCPScope.ALGORITHM,
            "algo_key": "thompson_bandit",
            "mode": RCPMode.ENFORCE,
            "authority_required": RCPAuthority.DG_AI,
            "hard_guards_json": {
                "min_weight": 0.005,  # Minimum 0.5% weight per destination
                "max_weight": 0.95  # Maximum 95% weight per destination
            },
            "soft_guards_json": {
                "exploration_bonus": 0.1  # Add 10% exploration bonus
            },
            "limits_json": {
                "max_arms": 50  # Maximum 50 destinations per smartlink
            },
            "gates_json": {
                "min_visits": 100  # Require at least 100 visits for optimization
            },
            "rollout_percent": 1.0,
            "enabled": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "UCB Bandit - Production Policy",
            "scope": RCPScope.ALGORITHM,
            "algo_key": "ucb_bandit",
            "mode": RCPMode.ENFORCE,
            "authority_required": RCPAuthority.DG_AI,
            "hard_guards_json": {
                "min_weight": 0.005,  # Minimum 0.5% weight per destination
                "max_weight": 0.95  # Maximum 95% weight per destination
            },
            "soft_guards_json": {
                "exploration_parameter": 1.0  # UCB exploration parameter
            },
            "limits_json": {
                "max_arms": 50  # Maximum 50 destinations per smartlink
            },
            "gates_json": {
                "min_visits": 100  # Require at least 100 visits for optimization
            },
            "rollout_percent": 1.0,
            "enabled": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Global Safety Policy",
            "scope": RCPScope.GLOBAL,
            "mode": RCPMode.ENFORCE,
            "authority_required": RCPAuthority.DG_AI,
            "hard_guards_json": {
                "max_concurrent_actions": 5,  # Maximum 5 concurrent actions
                "action_timeout_seconds": 30  # Actions timeout after 30 seconds
            },
            "soft_guards_json": {
                "logging_level": "INFO"  # Log at INFO level
            },
            "gates_json": {
                "system_health_check": True  # Require system health check
            },
            "rollout_percent": 1.0,
            "enabled": True
        }
    ]
    
    # Create policies
    for policy_data in default_policies:
        # Check if policy already exists
        existing = db.query(RCPPolicy).filter(
            RCPPolicy.algo_key == policy_data["algo_key"],
            RCPPolicy.scope == policy_data["scope"]
        ).first()
        
        if existing:
            print(f"Policy for {policy_data['algo_key']} already exists, skipping...")
            continue
        
        policy = RCPPolicy(**policy_data)
        db.add(policy)
        print(f"Created policy: {policy.name} for algorithm: {policy.algo_key}")
    
    # Commit changes
    db.commit()
    print("Default RCP policies initialized successfully!")

if __name__ == "__main__":
    create_default_policies()
