""
Tests for the SelfHealingAlgorithm.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from src.soft.dg.algorithms.maintenance.self_healing import SelfHealingAlgorithm
from src.soft.models.decision import DecisionContext, Action

@pytest.fixture
def healing():
    """Fixture that provides a SelfHealingAlgorithm instance with test config."""
    config = {
        "health_checks": {
            "api_errors": {
                "enabled": True,
                "threshold": 5,
                "time_window_minutes": 15,
                "actions": ["retry", "degrade", "alert"]
            },
            "high_latency": {
                "enabled": True,
                "threshold_ms": 1000,
                "actions": ["cache_more", "scale_up", "alert"]
            },
            "resource_usage": {
                "enabled": True,
                "cpu_threshold": 90,
                "memory_threshold": 90,
                "actions": ["scale_up", "cleanup", "alert"]
            }
        },
        "action_priorities": {
            "retry": 50,
            "degrade": 70,
            "alert": 90,
            "cache_more": 60,
            "scale_up": 80,
            "cleanup": 40
        },
        "alert_cooldown_minutes": 5,
        "max_concurrent_repairs": 3
    }
    return SelfHealingAlgorithm(), config

@pytest.mark.asyncio
async def test_api_error_check(healing):
    """Test API error detection and handling."""
    algo, config = healing
    
    # Create context with API errors
    context = DecisionContext(metrics={
        "api": {
            "error_count": 10,
            "total_requests": 100,
            "error_rate": 0.1
        }
    })
    
    result = await algo.execute(context, config)
    
    # Should generate multiple actions
    assert len(result.recommended_actions) >= 1
    assert any(a.action_type == "retry_failed_requests" for a in result.recommended_actions)
    assert any(a.action_type == "degrade_service" for a in result.recommended_actions)
    assert any(a.action_type == "create_alert" for a in result.recommended_actions)

@pytest.mark.asyncio
async def test_high_latency_check(healing):
    """Test high latency detection and handling."""
    algo, config = healing
    
    # Create context with high latency
    context = DecisionContext(metrics={
        "api": {
            "avg_latency_ms": 1500,
            "request_count": 1000
        }
    })
    
    result = await algo.execute(context, config)
    
    # Should generate actions for high latency
    assert len(result.recommended_actions) >= 1
    assert any("latency" in str(a).lower() for a in result.recommended_actions)

@pytest.mark.asyncio
async def test_resource_usage_check(healing):
    """Test resource usage detection and handling."""
    algo, config = healing
    
    # Create context with high resource usage
    context = DecisionContext(metrics={
        "system": {
            "cpu_percent": 95,
            "memory_percent": 85,
            "disk_percent": 70
        }
    })
    
    result = await algo.execute(context, config)
    
    # Should generate actions for high CPU
    assert len(result.recommended_actions) >= 1
    assert any("cpu" in str(a).lower() for a in result.recommended_actions)

@pytest.mark.asyncio
async def test_alert_cooldown(healing):
    """Test that alert cooldown works as expected."""
    algo, config = healing
    
    # First execution - should generate alerts
    context = DecisionContext(metrics={
        "api": {"error_count": 10, "total_requests": 100}
    })
    result1 = await algo.execute(context, config)
    assert len(result1.recommended_actions) > 0
    
    # Second execution with same issue - should be in cooldown
    result2 = await algo.execute(context, config)
    assert len(result2.recommended_actions) == 0

@pytest.mark.asyncio
async def test_concurrent_repairs_limit(healing):
    """Test that the number of concurrent repairs is limited."""
    algo, config = healing
    max_repairs = config["max_concurrent_repairs"]
    
    # Add max concurrent repairs
    for i in range(max_repairs):
        repair_id = f"repair_{i}"
        algo.active_repairs[repair_id] = {
            "started_at": datetime.utcnow(),
            "check": f"check_{i}",
            "action": Action(action_type=f"repair_{i}")
        }
    
    # Try to add one more repair
    context = DecisionContext(metrics={"api": {"error_count": 10}})
    result = await algo.execute(context, config)
    
    # Should not add more repairs
    assert len(algo.active_repairs) == max_repairs
    assert not any(a.action_type.startswith("repair_") for a in result.recommended_actions)

def test_cleanup_completed_repairs(healing):
    """Test that completed repairs are cleaned up properly."""
    algo, _ = healing
    
    # Add a stale repair
    repair_id = "stale_repair"
    algo.active_repairs[repair_id] = {
        "started_at": datetime.utcnow() - timedelta(hours=2),  # 2 hours old
        "check": "stale_check",
        "action": Action(action_type="cleanup_test")
    }
    
    # Run cleanup
    algo._cleanup_completed_repairs()
    
    # Stale repair should be removed
    assert repair_id not in algo.active_repairs

@pytest.mark.asyncio
async def test_disabled_checks(healing):
    """Test that disabled checks don't run."""
    algo, config = healing
    
    # Disable all checks
    for check in config["health_checks"].values():
        check["enabled"] = False
    
    # Create context that would trigger checks if they were enabled
    context = DecisionContext(metrics={
        "api": {"error_count": 10, "avg_latency_ms": 2000},
        "system": {"cpu_percent": 95}
    })
    
    result = await algo.execute(context, config)
    
    # No actions should be generated
    assert len(result.recommended_actions) == 0
