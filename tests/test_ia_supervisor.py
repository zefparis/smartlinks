"""
Tests for the IASupervisor module.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
import json

from src.soft.dg.ai.supervisor import IASupervisor, SupervisorState, AlgorithmRegistry
from src.soft.dg.ai.openai_integration import OpenAIIntegration
from src.soft.models.decision import DecisionContext, Action

# Test data
SAMPLE_ALGORITHMS = {
    "anomaly_detector": {
        "name": "anomaly_detector",
        "description": "Detects anomalies in system metrics",
    },
    "traffic_optimizer": {
        "name": "traffic_optimizer",
        "description": "Optimizes traffic routing",
    },
}

# Fixtures
@pytest.fixture
def mock_openai():
    with patch('src.soft.dg.ai.openai_integration.AsyncOpenAI') as mock:
        mock.return_value.chat.completions.create = AsyncMock(return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps({
                "summary": "Test analysis",
                "key_findings": ["Test finding 1", "Test finding 2"],
                "recommendations": ["Test recommendation 1"],
                "confidence_score": 0.9,
                "immediate_actions": [],
                "long_term_actions": []
            })))]
        ))
        yield mock

@pytest.fixture
def supervisor(mock_openai):
    return IASupervisor(
        openai_api_key="test-api-key",
        openai_model="gpt-4-test",
        algorithm_paths=[],
        initial_mode="auto"
    )

@pytest.fixture
def mock_algorithm():
    class MockAlgorithm:
        @classmethod
        def get_name(cls):
            return "test_algorithm"
            
        async def execute(self, context, config):
            return {
                "status": "success",
                "recommended_actions": [{"action_type": "test_action"}],
                "confidence": 0.9,
                "summary": "Test algorithm execution"
            }
    
    return MockAlgorithm()

# Tests
class TestSupervisorState:
    def test_initial_state(self):
        state = SupervisorState()
        assert state.mode == "auto"
        assert state.last_analysis_time is None
        assert state.active_actions == []
        assert state.metrics == {}
        assert state.alerts == []

class TestAlgorithmRegistry:
    def test_register_algorithm(self):
        registry = AlgorithmRegistry()
        registry.register(mock_algorithm)
        assert "test_algorithm" in registry._algorithms
        
    def test_get_algorithm(self, mock_algorithm):
        registry = AlgorithmRegistry()
        registry.register(mock_algorithm)
        algo = registry.get_algorithm("test_algorithm")
        assert algo is not None
        assert algo.get_name() == "test_algorithm"
        
    def test_get_nonexistent_algorithm(self):
        registry = AlgorithmRegistry()
        with pytest.raises(ValueError):
            registry.get_algorithm("nonexistent_algorithm")

class TestIASupervisor:
    @pytest.mark.asyncio
    async def test_analyze_system(self, supervisor, mock_algorithm):
        # Register a test algorithm
        supervisor.registry.register(mock_algorithm)
        
        # Test analysis
        result = await supervisor.analyze_system()
        
        # Verify results
        assert "test_algorithm" in result["results"]
        assert len(result["recommended_actions"]) > 0
        assert result["ai_analysis"]["summary"] == "Test analysis"
        
        # Verify state was updated
        assert supervisor.state.last_analysis_time is not None
        
    @pytest.mark.asyncio
    async def test_fix_detected_issues_auto_mode(self, supervisor, mock_algorithm):
        # Set up test data
        supervisor.state.mode = "auto"
        supervisor.registry.register(mock_algorithm)
        
        # Test fixing issues
        result = await supervisor.fix_detected_issues()
        
        # Verify results
        assert result["actions_executed"] > 0
        assert len(supervisor.state.active_actions) > 0
        
    @pytest.mark.asyncio
    async def test_fix_detected_issues_manual_mode(self, supervisor):
        # Set to manual mode
        supervisor.state.mode = "manual"
        
        # Test fixing issues (should not execute actions)
        result = await supervisor.fix_detected_issues()
        
        # Verify no actions were executed
        assert result["status"] == "error"
        
    @pytest.mark.asyncio
    async def test_ask_question(self, supervisor, mock_openai):
        # Test asking a question
        response = await supervisor.ask("What is the status?")
        
        # Verify response
        assert "question" in response
        assert "response" in response
        assert "timestamp" in response
        
    def test_set_mode(self, supervisor):
        # Test switching to manual mode
        supervisor.set_mode("manual")
        assert supervisor.state.mode == "manual"
        
        # Test invalid mode
        with pytest.raises(ValueError):
            supervisor.set_mode("invalid_mode")
            
    def test_get_status(self, supervisor):
        # Set some test data
        supervisor.state.last_analysis_time = datetime.utcnow()
        supervisor.state.active_actions = [{"action": "test_action"}]
        
        # Get status
        status = supervisor.get_status()
        
        # Verify status
        assert status["mode"] == "auto"
        assert status["active_actions"] == 1
        assert "last_analysis_time" in status
        
    @pytest.mark.asyncio
    async def test_extract_recommended_actions(self, supervisor, mock_algorithm):
        # Register a test algorithm
        supervisor.registry.register(mock_algorithm)
        
        # Create test results
        results = {
            "test_algorithm": {
                "recommended_actions": [
                    {"action_type": "test_action", "priority": 1}
                ]
            }
        }
        
        # Extract actions
        actions = supervisor._extract_recommended_actions(results)
        
        # Verify actions
        assert len(actions) == 1
        assert actions[0]["action_type"] == "test_action"
        assert actions[0]["source_algorithm"] == "test_algorithm"

# Integration test for the full flow
@pytest.mark.integration
class TestIASupervisorIntegration:
    @pytest.mark.asyncio
    async def test_full_flow(self, supervisor, mock_algorithm, mock_openai):
        # 1. Initialize
        supervisor.registry.register(mock_algorithm)
        
        # 2. Analyze system
        analysis = await supervisor.analyze_system()
        assert analysis["ai_analysis"]["summary"] == "Test analysis"
        
        # 3. Fix issues (in auto mode)
        fix_result = await supervisor.fix_detected_issues()
        assert fix_result["actions_executed"] > 0
        
        # 4. Switch to manual mode
        supervisor.set_mode("manual")
        assert supervisor.state.mode == "manual"
        
        # 5. Get status
        status = supervisor.get_status()
        assert status["mode"] == "manual"
        assert status["active_actions"] > 0
        
        # 6. Ask a question
        response = await supervisor.ask("What's the current status?")
        assert "response" in response
        
        # 7. Verify logs
        assert len(supervisor.state.metrics.get("interaction_log", [])) > 0

# Test error handling
@pytest.mark.asyncio
async def test_error_handling(supervisor):
    # Test with an algorithm that raises an exception
    class ErrorAlgorithm:
        @classmethod
        def get_name(cls):
            return "error_algorithm"
            
        async def execute(self, context, config):
            raise ValueError("Test error")
    
    # Register the error algorithm
    supervisor.registry.register(ErrorAlgorithm())
    
    # Test that the error is caught and logged
    result = await supervisor.analyze_system()
    assert "error_algorithm" in result["results"]
    assert "error" in result["results"]["error_algorithm"]
    
    # Test invalid mode setting
    with pytest.raises(ValueError):
        supervisor.set_mode("invalid_mode")
