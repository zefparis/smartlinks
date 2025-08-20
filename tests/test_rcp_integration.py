"""
Integration tests for RCP system with autopilot runner.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from src.soft.autopilot.runner import AlgorithmRunner
from src.soft.rcp.models import RCPPolicy, RCPScope, RCPMode, AuthorityLevel
from src.soft.rcp.schemas import ActionDTO


class TestRCPIntegration:
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_db_session_factory = Mock()
        self.runner = AlgorithmRunner(self.mock_db_session_factory)
        
        # Mock database session
        self.mock_db = Mock()
        self.mock_db_session_factory.return_value.__enter__.return_value = self.mock_db
        self.mock_db_session_factory.return_value.__exit__.return_value = None

    @pytest.mark.asyncio
    @patch('src.soft.autopilot.runner.RCPRepository')
    async def test_rcp_integration_with_runner(self, mock_repo_class):
        """Test RCP integration with algorithm runner."""
        # Setup mocks
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Mock policy that blocks high-risk actions
        mock_policy = Mock()
        mock_policy.id = "safety-policy"
        mock_repo.get_applicable_policies.return_value = [mock_policy]
        
        # Mock RCP result that blocks one action
        mock_rcp_result = Mock()
        mock_rcp_result.allowed = []
        mock_rcp_result.modified = []
        mock_rcp_result.blocked = [Mock()]
        mock_rcp_result.risk_cost = 5.0
        mock_rcp_result.notes = ["Action blocked by safety policy"]
        
        with patch.object(self.runner.rcp_evaluator, 'evaluate_policies', return_value=mock_rcp_result):
            with patch.object(self.runner, 'load_algorithm_settings', return_value={"active": True}):
                with patch.object(self.runner, 'load_ai_policy', return_value={"authority_level": "admin"}):
                    with patch.object(self.runner, '_generate_algorithm_actions', return_value=[{"type": "reweight", "risk_score": 8.0}]):
                        with patch.object(self.runner, 'execute_action', return_value=True):
                            with patch.object(self.runner, 'audit_action', return_value=None):
                                with patch.object(self.runner, '_update_algorithm_run', return_value=None):
                                    
                                    result = await self.runner.run_algorithm("traffic_optimizer")
                                    
                                    # Verify RCP was applied
                                    assert result["rcp_applied"] is True
                                    assert result["rcp_risk_cost"] == 5.0
                                    assert result["executed_actions"] == 0  # No actions executed due to blocking

    @pytest.mark.asyncio
    async def test_manual_override_bypasses_rcp(self):
        """Test that manual override bypasses RCP evaluation."""
        with patch.object(self.runner, 'load_algorithm_settings', return_value={"active": True}):
            with patch.object(self.runner, 'load_ai_policy', return_value={"authority_level": "admin"}):
                with patch.object(self.runner, '_generate_algorithm_actions', return_value=[{"type": "reweight", "risk_score": 8.0}]):
                    with patch.object(self.runner, 'execute_action', return_value=True):
                        with patch.object(self.runner, '_update_algorithm_run', return_value=None):
                            
                            result = await self.runner.run_algorithm("traffic_optimizer", manual_override=True)
                            
                            # Verify RCP was not applied
                            assert result["rcp_applied"] is False
                            assert result["rcp_risk_cost"] == 0.0

    @pytest.mark.asyncio
    @patch('src.soft.autopilot.runner.RCPRepository')
    async def test_rcp_action_modification(self, mock_repo_class):
        """Test RCP modifying actions before execution."""
        # Setup mocks
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_applicable_policies.return_value = [Mock()]
        
        # Mock RCP result that modifies actions
        modified_action = ActionDTO(
            id="modified-001",
            type="reweight",
            algo_key="traffic_optimizer",
            idempotency_key="key-001",
            data={"weight": 0.7},  # Modified from original 0.8
            risk_score=2.0
        )
        
        mock_rcp_result = Mock()
        mock_rcp_result.allowed = []
        mock_rcp_result.modified = [modified_action]
        mock_rcp_result.blocked = []
        mock_rcp_result.risk_cost = 2.0
        mock_rcp_result.notes = ["Weight reduced by safety policy"]
        
        with patch.object(self.runner.rcp_evaluator, 'evaluate_policies', return_value=mock_rcp_result):
            with patch.object(self.runner, 'load_algorithm_settings', return_value={"active": True}):
                with patch.object(self.runner, 'load_ai_policy', return_value={"authority_level": "admin"}):
                    with patch.object(self.runner, '_generate_algorithm_actions', return_value=[{"type": "reweight", "weight": 0.8, "risk_score": 3.0}]):
                        with patch.object(self.runner, 'execute_action', return_value=True) as mock_execute:
                            with patch.object(self.runner, '_update_algorithm_run', return_value=None):
                                
                                result = await self.runner.run_algorithm("traffic_optimizer")
                                
                                # Verify modified action was executed
                                assert result["executed_actions"] == 1
                                assert result["rcp_applied"] is True
                                
                                # Check that execute_action was called with modified data
                                executed_data = mock_execute.call_args[0][1]
                                assert executed_data["weight"] == 0.7

    @pytest.mark.asyncio
    async def test_rcp_evaluation_error_handling(self):
        """Test error handling in RCP evaluation."""
        with patch.object(self.runner, 'load_algorithm_settings', return_value={"active": True}):
            with patch.object(self.runner, 'load_ai_policy', return_value={"authority_level": "admin"}):
                with patch.object(self.runner, '_generate_algorithm_actions', return_value=[{"type": "reweight", "risk_score": 2.0}]):
                    with patch.object(self.runner, '_apply_rcp_policies', side_effect=Exception("RCP error")):
                        with patch.object(self.runner, 'execute_action', return_value=True):
                            with patch.object(self.runner, '_update_algorithm_run', return_value=None):
                                
                                # Should not crash, should continue without RCP
                                result = await self.runner.run_algorithm("traffic_optimizer")
                                
                                assert result["status"] == "completed"
                                assert result["rcp_applied"] is False

    @pytest.mark.asyncio
    @patch('src.soft.autopilot.runner.RCPRepository')
    async def test_rcp_audit_logging(self, mock_repo_class):
        """Test RCP audit logging functionality."""
        # Setup mocks
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_applicable_policies.return_value = [Mock()]
        mock_repo.create_evaluation.return_value = Mock()
        
        # Mock RCP result with blocked action
        blocked_action = ActionDTO(
            id="blocked-001",
            type="reweight",
            algo_key="traffic_optimizer",
            idempotency_key="key-001",
            data={"weight": 0.9, "risk_score": 10.0},
            risk_score=10.0
        )
        
        mock_rcp_result = Mock()
        mock_rcp_result.allowed = []
        mock_rcp_result.modified = []
        mock_rcp_result.blocked = [blocked_action]
        mock_rcp_result.risk_cost = 0.0
        mock_rcp_result.notes = ["Action blocked due to high risk"]
        
        with patch.object(self.runner.rcp_evaluator, 'evaluate_policies', return_value=mock_rcp_result):
            with patch.object(self.runner, 'load_algorithm_settings', return_value={"active": True}):
                with patch.object(self.runner, 'load_ai_policy', return_value={"authority_level": "admin"}):
                    with patch.object(self.runner, '_generate_algorithm_actions', return_value=[{"type": "reweight", "weight": 0.9, "risk_score": 10.0}]):
                        with patch.object(self.runner, 'audit_action', return_value=None) as mock_audit:
                            with patch.object(self.runner, '_update_algorithm_run', return_value=None):
                                
                                result = await self.runner.run_algorithm("traffic_optimizer")
                                
                                # Verify audit logging was called for blocked action
                                mock_audit.assert_called_with("traffic_optimizer", blocked_action.data, "blocked_by_rcp")

    @pytest.mark.asyncio
    async def test_rcp_metrics_integration(self):
        """Test RCP integration with metrics collection."""
        mock_metrics = {
            "cvr_1h": 0.045,
            "cvr_24h_mean": 0.048,
            "traffic_volume": 1000.0,
            "error_rate": 0.01
        }
        
        mock_segment_data = {
            "geo": "US",
            "device": "mobile",
            "source": "organic"
        }
        
        with patch.object(self.runner, '_get_current_metrics', return_value=mock_metrics):
            with patch.object(self.runner, '_get_segment_data', return_value=mock_segment_data):
                with patch.object(self.runner, 'load_algorithm_settings', return_value={"active": True}):
                    with patch.object(self.runner, 'load_ai_policy', return_value={"authority_level": "admin"}):
                        with patch.object(self.runner, '_generate_algorithm_actions', return_value=[]):
                            with patch.object(self.runner, '_update_algorithm_run', return_value=None):
                                
                                # Test that metrics are properly collected
                                metrics = await self.runner._get_current_metrics("traffic_optimizer")
                                segment_data = await self.runner._get_segment_data("traffic_optimizer")
                                
                                assert metrics["cvr_1h"] == 0.045
                                assert segment_data["device"] == "mobile"

    @pytest.mark.asyncio
    async def test_algorithm_run_record_update(self):
        """Test algorithm run record updates with RCP information."""
        with patch.object(self.runner, 'load_algorithm_settings', return_value={"active": True, "version": 2}):
            with patch.object(self.runner, 'load_ai_policy', return_value={"authority_level": "safe_apply"}):
                with patch.object(self.runner, '_generate_algorithm_actions', return_value=[]):
                    with patch.object(self.runner, '_apply_rcp_policies', return_value=None):
                        with patch.object(self.runner, '_update_algorithm_run', return_value=None) as mock_update:
                            
                            result = await self.runner.run_algorithm("traffic_optimizer")
                            
                            # Verify algorithm run record was updated with RCP info
                            mock_update.assert_called_once()
                            call_args = mock_update.call_args[1]
                            assert call_args["algo_key"] == "traffic_optimizer"
                            assert call_args["settings_version"] == 2
                            assert call_args["ai_authority_used"] == "safe_apply"
                            assert "rcp_applied" in call_args

    @pytest.mark.asyncio
    async def test_rcp_performance_impact(self):
        """Test RCP performance impact on algorithm execution."""
        import time
        
        with patch.object(self.runner, 'load_algorithm_settings', return_value={"active": True}):
            with patch.object(self.runner, 'load_ai_policy', return_value={"authority_level": "admin"}):
                with patch.object(self.runner, '_generate_algorithm_actions', return_value=[]):
                    with patch.object(self.runner, '_apply_rcp_policies', return_value=None):
                        with patch.object(self.runner, '_update_algorithm_run', return_value=None):
                            
                            start_time = time.time()
                            result = await self.runner.run_algorithm("traffic_optimizer")
                            end_time = time.time()
                            
                            # Verify execution completes in reasonable time
                            execution_time = end_time - start_time
                            assert execution_time < 1.0  # Should complete within 1 second
                            assert result["status"] == "completed"
