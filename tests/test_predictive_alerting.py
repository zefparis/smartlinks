""
Tests for the PredictiveAlerting algorithm.
"""
import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from src.soft.dg.algorithms.monitoring.predictive_alerting import PredictiveAlerting
from src.soft.models.decision import DecisionContext

@pytest.fixture
def alerting():
    """Fixture that provides a PredictiveAlerting instance with test config."""
    config = {
        "metrics_to_monitor": ["response_time"],
        "thresholds": {
            "response_time": {"warning": 100, "critical": 200}
        },
        "trend_analysis": {
            "window_size": 3,
            "increasing_trend_threshold": 0.2,
            "decreasing_trend_threshold": -0.2
        },
        "anomaly_detection": {
            "contamination": 0.1,
            "n_estimators": 10,
            "random_state": 42,
            "training_window_days": 1
        },
        "alert_cooldown_minutes": 5
    }
    return PredictiveAlerting(), config

@pytest.mark.asyncio
async def test_threshold_alerting(alerting):
    """Test that threshold-based alerts are triggered correctly."""
    algo, config = alerting
    
    # Test warning threshold
    context = DecisionContext(metrics={"response_time": 110})
    result = await algo.execute(context, config)
    assert len(result.recommended_actions) == 1
    assert "warning" in result.recommended_actions[0].description.lower()
    
    # Test critical threshold
    context = DecisionContext(metrics={"response_time": 210})
    result = await algo.execute(context, config)
    assert len(result.recommended_actions) == 1
    assert "critical" in result.recommended_actions[0].description.lower()

@pytest.mark.asyncio
async def test_trend_detection(alerting):
    """Test that trend detection works as expected."""
    algo, config = alerting
    
    # Create an increasing trend
    for i in range(5):
        context = DecisionContext(metrics={"response_time": 50 + i*20})
        await algo.execute(context, config)
    
    # Should detect increasing trend
    context = DecisionContext(metrics={"response_time": 150})
    result = await algo.execute(context, config)
    assert any("increasing trend" in str(a) for a in result.recommended_actions)

@pytest.mark.asyncio
async def test_anomaly_detection(alerting):
    """Test that anomaly detection works as expected."""
    algo, config = alerting
    
    # Train with normal data
    for _ in range(20):
        context = DecisionContext(metrics={"response_time": 50 + np.random.normal(0, 5)})
        await algo.execute(context, config)
    
    # Test with anomaly
    context = DecisionContext(metrics={"response_time": 200})
    result = await algo.execute(context, config)
    assert any("anomaly" in str(a).lower() for a in result.recommended_actions)

@pytest.mark.asyncio
async def test_alert_cooldown(alerting):
    """Test that alert cooldown works as expected."""
    algo, config = alerting
    
    # First alert should be generated
    context = DecisionContext(metrics={"response_time": 110})
    result = await algo.execute(context, config)
    assert len(result.recommended_actions) > 0
    
    # Second alert should be suppressed by cooldown
    result = await algo.execute(context, config)
    assert len(result.recommended_actions) == 0

def test_confidence_calculation(alerting):
    """Test that confidence calculations are correct."""
    algo, config = alerting
    
    # Test with high confidence
    alert = MagicMock()
    alert.metadata = {"confidence": 0.9}
    assert algo._is_above_confidence(alert, config) is True
    
    # Test with low confidence
    alert.metadata = {"confidence": 0.5}
    assert algo._is_above_confidence(alert, config) is False

@pytest.mark.asyncio
async def test_historical_data_tracking(alerting):
    """Test that historical data is tracked correctly."""
    algo, config = alerting
    
    # Add some data points
    for i in range(5):
        context = DecisionContext(metrics={"response_time": i * 10})
        await algo.execute(context, config)
    
    # Check that historical data was tracked
    assert len(algo.historical_data["response_time"]) == 5
    
    # Check that old data is pruned
    old_time = datetime.utcnow() - timedelta(days=2)
    algo.historical_data["response_time"][0]["timestamp"] = old_time
    
    context = DecisionContext(metrics={"response_time": 50})
    await algo.execute(context, config)
    
    # Old data point should be removed
    assert all(point["timestamp"] > old_time for point in algo.historical_data["response_time"])

@pytest.mark.asyncio
async def test_metric_not_monitored(alerting):
    """Test that unmonitored metrics are ignored."""
    algo, config = alerting
    
    # This metric is not in metrics_to_monitor
    context = DecisionContext(metrics={"unmonitored_metric": 1000})
    result = await algo.execute(context, config)
    
    # No alerts should be generated
    assert len(result.recommended_actions) == 0
