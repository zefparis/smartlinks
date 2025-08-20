""
Tests for the TrafficSimulator algorithm.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from src.soft.dg.algorithms.simulation.traffic_simulator import TrafficSimulator
from src.soft.models.decision import DecisionContext, Action

@pytest.fixture
def traffic_sim():
    """Fixture that provides a TrafficSimulator instance with test config."""
    config = {
        "simulation_duration_hours": 24,
        "resolution_minutes": 5,
        "baseline_traffic": 1000,
        "patterns": [
            {
                "type": "weekly",
                "amplitude": 0.5,
                "phase_shift": 0,
                "periods_per_week": 1
            },
            {
                "type": "spike",
                "start_hour": 12,
                "duration_hours": 2,
                "intensity": 3.0
            }
        ],
        "anomaly_detection": {
            "sensitivity": 2.0,
            "window_size": 6,
            "min_anomaly_duration": 2
        },
        "seed": 42
    }
    return TrafficSimulator(), config

@pytest.mark.asyncio
async def test_generate_traffic_pattern(traffic_sim):
    """Test traffic pattern generation."""
    algo, config = traffic_sim
    
    # Generate traffic for a day
    timestamps, traffic = algo._generate_traffic_pattern(
        duration_hours=24,
        resolution_minutes=config["resolution_minutes"],
        baseline=config["baseline_traffic"],
        patterns=config["patterns"]
    )
    
    # Should generate correct number of points
    expected_points = (24 * 60) // config["resolution_minutes"]
    assert len(timestamps) == expected_points
    assert len(traffic) == expected_points
    
    # Traffic should never be negative
    assert all(t >= 0 for t in traffic)
    
    # Should have a spike around noon
    noon_index = 12 * (60 // config["resolution_minutes"])
    assert traffic[noon_index] > config["baseline_traffic"] * 2.5

@pytest.mark.asyncio
async def test_detect_anomalies(traffic_sim):
    """Test anomaly detection in traffic data."""
    algo, config = traffic_sim
    
    # Create test data with an anomaly
    timestamps = [datetime(2023, 1, 1) + timedelta(hours=i) for i in range(24)]
    traffic = [1000] * 24
    traffic[12] = 5000  # Anomalous spike at noon
    
    anomalies = algo._detect_anomalies(
        timestamps=timestamps,
        traffic=traffic,
        sensitivity=config["anomaly_detection"]["sensitivity"],
        window_size=config["anomaly_detection"]["window_size"]
    )
    
    # Should detect the spike at noon
    assert len(anomalies) > 0
    assert any(12 <= a["hour"] < 13 for a in anomalies)

@pytest.mark.asyncio
async def test_execute(traffic_sim):
    """Test the main execute method."""
    algo, config = traffic_sim
    
    # Mock the internal methods to return known values
    with patch.object(algo, '_generate_traffic_pattern') as mock_gen, \
         patch.object(algo, '_detect_anomalies') as mock_detect:
        
        # Setup mocks
        mock_gen.return_value = (
            [datetime(2023, 1, 1) + timedelta(hours=i) for i in range(24)],
            [1000] * 24
        )
        
        mock_detect.return_value = [{
            "start_time": datetime(2023, 1, 1, 12),
            "end_time": datetime(2023, 1, 1, 13),
            "hour": 12,
            "severity": "high",
            "description": "Test anomaly"
        }]
        
        # Execute
        context = DecisionContext()
        result = await algo.execute(context, config)
        
        # Verify results
        assert len(result.recommended_actions) > 0
        assert any("anomaly" in str(a).lower() for a in result.recommended_actions)
        assert result.metadata["anomalies_detected"] == 1

@pytest.mark.asyncio
async def test_anomaly_actions(traffic_sim):
    """Test that appropriate actions are generated for anomalies."""
    algo, config = traffic_sim
    
    # Create a test anomaly
    anomaly = {
        "start_time": datetime(2023, 1, 1, 12),
        "end_time": datetime(2023, 1, 1, 13),
        "hour": 12,
        "severity": "high",
        "description": "Test anomaly"
    }
    
    actions = algo._generate_anomaly_actions(anomaly, config)
    
    # Should generate appropriate actions
    assert len(actions) > 0
    assert any(a.action_type == "scale_service" for a in actions)
    assert any("investigate" in str(a).lower() for a in actions)

def test_generate_weekly_pattern():
    """Test weekly pattern generation."""
    algo = TrafficSimulator()
    
    # Generate a weekly pattern with known parameters
    hours = np.linspace(0, 24*7, 100)  # One week of data
    pattern = algo._generate_weekly_pattern(
        hours=hours,
        baseline=1000,
        amplitude=0.5,
        phase_shift=0,
        periods_per_week=1
    )
    
    # Should have expected shape and range
    assert len(pattern) == len(hours)
    assert 500 <= min(pattern) <= 1500
    assert 500 <= max(pattern) <= 1500
    
    # Should be periodic with 1 week period
    assert abs(pattern[0] - pattern[-1]) < 1e-6  # Start and end should be similar

def test_generate_spike_pattern():
    """Test spike pattern generation."""
    algo = TrafficSimulator()
    
    # Generate a spike pattern
    hours = np.linspace(0, 24, 100)  # One day of data
    pattern = algo._generate_spike_pattern(
        hours=hours,
        baseline=1000,
        start_hour=12,
        duration_hours=2,
        intensity=3.0
    )
    
    # Should have expected shape and range
    assert len(pattern) == len(hours)
    assert min(pattern) >= 1000  # Never below baseline
    assert max(pattern) >= 2500  # Should reach at least 2.5x baseline
    
    # Should have peak at 13:00 (middle of spike)
    peak_index = np.argmax(pattern)
    peak_hour = hours[peak_index]
    assert 12.5 <= peak_hour <= 13.5
