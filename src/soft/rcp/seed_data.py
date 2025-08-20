"""
Seed data for Runtime Control Policies (RCP).
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import RCPPolicy, RCPScope, RCPMode, AuthorityLevel

def create_seed_policies(db: Session):
    """Create example RCP policies for demonstration and testing."""
    
    # Global safety policy
    global_safety = RCPPolicy(
        id="global-safety-001",
        name="Global Safety Guards",
        description="Global safety guards to prevent dangerous algorithm actions",
        scope=RCPScope.GLOBAL,
        mode=RCPMode.ENFORCE,
        enabled=True,
        authority_required=AuthorityLevel.DG_AI,
        guards={
            "hard_guards": [
                {
                    "name": "cvr_minimum",
                    "condition": "metrics.cvr_1h >= 0.02",
                    "message": "CVR too low - blocking all actions"
                },
                {
                    "name": "error_rate_maximum", 
                    "condition": "metrics.error_rate <= 0.10",
                    "message": "Error rate too high - blocking all actions"
                }
            ],
            "soft_guards": [
                {
                    "name": "cvr_warning",
                    "condition": "metrics.cvr_1h >= 0.03",
                    "message": "CVR below optimal - consider caution"
                }
            ]
        },
        limits={
            "rate_limits": [
                {
                    "name": "global_actions_per_hour",
                    "limit": 50,
                    "window_minutes": 60,
                    "scope": "global"
                }
            ],
            "risk_limits": [
                {
                    "name": "max_risk_per_action",
                    "limit": 10.0,
                    "message": "Action risk too high"
                }
            ]
        },
        gates={
            "time_gates": [
                {
                    "name": "business_hours_only",
                    "schedule": "0 9-17 * * 1-5",
                    "timezone": "Europe/Paris",
                    "enabled": False
                }
            ],
            "condition_gates": [
                {
                    "name": "traffic_volume_gate",
                    "condition": "metrics.traffic_volume >= 500",
                    "message": "Traffic volume too low for safe operation"
                }
            ]
        },
        mutations={
            "weight_mutations": [
                {
                    "name": "conservative_weights",
                    "condition": "metrics.cvr_1h < 0.04",
                    "action": "clamp",
                    "field": "weight",
                    "max_value": 0.8,
                    "message": "Reducing weights due to low CVR"
                }
            ],
            "delta_mutations": [
                {
                    "name": "limit_large_changes",
                    "max_delta_percent": 20,
                    "fields": ["weight", "bid"],
                    "message": "Limiting large changes"
                }
            ]
        },
        scheduling={
            "enabled": True,
            "cron": "*/15 * * * *",  # Every 15 minutes
            "timezone": "UTC"
        },
        rollout={
            "enabled": True,
            "percentage": 100,
            "strategy": "random"
        },
        expiration=datetime.now() + timedelta(days=365),
        metadata={
            "created_by": "system",
            "purpose": "Global safety enforcement",
            "contact": "dg-ai-team@company.com"
        },
        created_at=datetime.now(),
        updated_at=datetime.now(),
        updated_by="system"
    )

    # Traffic optimizer specific policy
    traffic_optimizer_policy = RCPPolicy(
        id="traffic-optimizer-001",
        name="Traffic Optimizer Controls",
        description="Specific controls for traffic optimization algorithm",
        scope=RCPScope.ALGORITHM,
        selector={"algo_key": "traffic_optimizer"},
        mode=RCPMode.MONITOR,
        enabled=True,
        authority_required=AuthorityLevel.ADMIN,
        guards={
            "soft_guards": [
                {
                    "name": "reweight_frequency",
                    "condition": "action.type != 'reweight' or last_reweight_minutes >= 30",
                    "message": "Reweight actions too frequent"
                }
            ]
        },
        limits={
            "rate_limits": [
                {
                    "name": "traffic_actions_per_hour",
                    "limit": 20,
                    "window_minutes": 60,
                    "scope": "algorithm"
                }
            ]
        },
        gates={
            "condition_gates": [
                {
                    "name": "segment_performance_gate",
                    "condition": "segment_data.performance_score >= 0.7",
                    "message": "Segment performance too low"
                }
            ]
        },
        mutations={
            "weight_mutations": [
                {
                    "name": "gradual_weight_changes",
                    "action": "clamp_delta",
                    "field": "weight",
                    "max_delta": 0.1,
                    "message": "Limiting weight change magnitude"
                }
            ]
        },
        scheduling={
            "enabled": True,
            "cron": "*/5 * * * *",  # Every 5 minutes
            "timezone": "UTC"
        },
        rollout={
            "enabled": True,
            "percentage": 80,  # Canary rollout
            "strategy": "hash_based"
        },
        expiration=datetime.now() + timedelta(days=90),
        metadata={
            "created_by": "traffic_team",
            "purpose": "Traffic optimization safety",
            "algorithm_version": "v2.1"
        },
        created_at=datetime.now(),
        updated_at=datetime.now(),
        updated_by="traffic_team"
    )

    # Segment-specific policy for mobile users
    mobile_segment_policy = RCPPolicy(
        id="mobile-segment-001",
        name="Mobile Segment Protection",
        description="Special protections for mobile user segments",
        scope=RCPScope.SEGMENT,
        selector={"segment_data.device": "mobile"},
        mode=RCPMode.ENFORCE,
        enabled=True,
        authority_required=AuthorityLevel.OPERATOR,
        guards={
            "hard_guards": [
                {
                    "name": "mobile_cvr_protection",
                    "condition": "metrics.mobile_cvr_1h >= 0.025",
                    "message": "Mobile CVR too low - protecting mobile users"
                }
            ]
        },
        limits={
            "risk_limits": [
                {
                    "name": "mobile_risk_limit",
                    "limit": 3.0,
                    "message": "Risk limit for mobile segment"
                }
            ]
        },
        mutations={
            "weight_mutations": [
                {
                    "name": "mobile_conservative_weights",
                    "action": "multiply",
                    "field": "weight",
                    "factor": 0.9,
                    "message": "Conservative weights for mobile"
                }
            ]
        },
        scheduling={
            "enabled": True,
            "cron": "*/10 * * * *",
            "timezone": "UTC"
        },
        rollout={
            "enabled": True,
            "percentage": 100,
            "strategy": "random"
        },
        expiration=datetime.now() + timedelta(days=180),
        metadata={
            "created_by": "mobile_team",
            "purpose": "Mobile user protection",
            "segment": "mobile_users"
        },
        created_at=datetime.now(),
        updated_at=datetime.now(),
        updated_by="mobile_team"
    )

    # Emergency circuit breaker policy
    emergency_breaker = RCPPolicy(
        id="emergency-breaker-001",
        name="Emergency Circuit Breaker",
        description="Emergency policy to stop all algorithm actions in crisis",
        scope=RCPScope.GLOBAL,
        mode=RCPMode.ENFORCE,
        enabled=False,  # Disabled by default, activated in emergencies
        authority_required=AuthorityLevel.DG_AI,
        guards={
            "hard_guards": [
                {
                    "name": "emergency_stop",
                    "condition": "false",  # Always blocks when enabled
                    "message": "EMERGENCY: All algorithm actions suspended"
                }
            ]
        },
        limits={},
        gates={},
        mutations={},
        scheduling={
            "enabled": False
        },
        rollout={
            "enabled": True,
            "percentage": 100,
            "strategy": "immediate"
        },
        expiration=datetime.now() + timedelta(days=30),  # Short expiration
        metadata={
            "created_by": "system",
            "purpose": "Emergency circuit breaker",
            "activation": "manual_only",
            "escalation": "immediate"
        },
        created_at=datetime.now(),
        updated_at=datetime.now(),
        updated_by="system"
    )

    # Add all policies to session
    policies = [
        global_safety,
        traffic_optimizer_policy,
        mobile_segment_policy,
        emergency_breaker
    ]

    for policy in policies:
        # Check if policy already exists
        existing = db.query(RCPPolicy).filter(RCPPolicy.id == policy.id).first()
        if not existing:
            db.add(policy)
    
    db.commit()
    return len(policies)


def get_example_policy_templates():
    """Get example policy templates for documentation."""
    return {
        "basic_guard_policy": {
            "id": "example-guard-001",
            "name": "Basic Guard Example",
            "description": "Example of basic guard implementation",
            "scope": "algorithm",
            "selector": {"algo_key": "your_algorithm"},
            "mode": "monitor",
            "enabled": True,
            "authority_required": "admin",
            "guards": {
                "hard_guards": [
                    {
                        "name": "minimum_performance",
                        "condition": "metrics.performance_score >= 0.8",
                        "message": "Performance too low"
                    }
                ],
                "soft_guards": [
                    {
                        "name": "warning_threshold",
                        "condition": "metrics.performance_score >= 0.9",
                        "message": "Performance below optimal"
                    }
                ]
            }
        },
        "rate_limit_policy": {
            "id": "example-limits-001",
            "name": "Rate Limiting Example",
            "description": "Example of rate limiting implementation",
            "scope": "global",
            "mode": "enforce",
            "enabled": True,
            "authority_required": "operator",
            "limits": {
                "rate_limits": [
                    {
                        "name": "actions_per_hour",
                        "limit": 100,
                        "window_minutes": 60,
                        "scope": "global"
                    }
                ],
                "risk_limits": [
                    {
                        "name": "max_risk_per_action",
                        "limit": 5.0,
                        "message": "Action risk exceeds limit"
                    }
                ]
            }
        },
        "mutation_policy": {
            "id": "example-mutations-001",
            "name": "Mutation Example",
            "description": "Example of action mutations",
            "scope": "algorithm",
            "selector": {"algo_key": "your_algorithm"},
            "mode": "enforce",
            "enabled": True,
            "authority_required": "admin",
            "mutations": {
                "weight_mutations": [
                    {
                        "name": "conservative_scaling",
                        "condition": "metrics.confidence < 0.8",
                        "action": "multiply",
                        "field": "weight",
                        "factor": 0.8,
                        "message": "Scaling down due to low confidence"
                    }
                ],
                "delta_mutations": [
                    {
                        "name": "limit_changes",
                        "max_delta_percent": 15,
                        "fields": ["weight", "bid"],
                        "message": "Limiting change magnitude"
                    }
                ]
            }
        }
    }
