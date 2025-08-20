"""
Tests for RCP evaluator functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from src.soft.rcp.evaluator import RCPEvaluator
from src.soft.rcp.schemas import (
    RCPPolicy, RCPEvaluationContext, ActionDTO,
    RCPGuards, RCPLimits, RCPGates, RCPMutations,
    RCPScheduling, RCPRollout
)


class TestRCPEvaluator:
    
    def setup_method(self):
        """Setup test fixtures."""
        self.evaluator = RCPEvaluator()
        
        # Sample action
        self.sample_action = ActionDTO(
            id="action-001",
            type="reweight",
            algo_key="traffic_optimizer",
            idempotency_key="test-key-001",
            data={
                "target": "destination_123",
                "weight": 0.8,
                "previous_weight": 0.6
            },
            risk_score=2.5
        )
        
        # Sample context
        self.sample_context = RCPEvaluationContext(
            algo_key="traffic_optimizer",
            metrics={
                "cvr_1h": 0.045,
                "cvr_24h_mean": 0.048,
                "traffic_volume": 1000.0,
                "error_rate": 0.01
            },
            segment_data={
                "geo": "US",
                "device": "desktop",
                "source": "organic"
            },
            manual_override_active=False
        )

    def test_manual_override_bypass(self):
        """Test that manual override bypasses all RCP evaluation."""
        policy = RCPPolicy(
            id="test-policy",
            name="Test Policy",
            scope="global",
            mode="enforce",
            enabled=True,
            authority_required="admin",
            guards=RCPGuards(
                hard_guards=[{
                    "name": "always_block",
                    "condition": "false",
                    "message": "Always blocks"
                }]
            )
        )
        
        context = self.sample_context.copy()
        context.manual_override_active = True
        
        result = self.evaluator.evaluate_policies(
            context, [policy], [self.sample_action]
        )
        
        assert len(result.allowed) == 1
        assert len(result.blocked) == 0
        assert "Manual override active" in result.notes

    def test_hard_guard_blocks_action(self):
        """Test that hard guards block actions when conditions fail."""
        policy = RCPPolicy(
            id="test-policy",
            name="Test Policy",
            scope="global",
            mode="enforce",
            enabled=True,
            authority_required="admin",
            guards=RCPGuards(
                hard_guards=[{
                    "name": "cvr_minimum",
                    "condition": "metrics.cvr_1h >= 0.05",
                    "message": "CVR too low"
                }]
            )
        )
        
        # CVR is 0.045, below the 0.05 threshold
        result = self.evaluator.evaluate_policies(
            self.sample_context, [policy], [self.sample_action]
        )
        
        assert len(result.blocked) == 1
        assert len(result.allowed) == 0
        assert "CVR too low" in result.notes

    def test_soft_guard_allows_with_warning(self):
        """Test that soft guards allow actions but generate warnings."""
        policy = RCPPolicy(
            id="test-policy",
            name="Test Policy",
            scope="global",
            mode="enforce",
            enabled=True,
            authority_required="admin",
            guards=RCPGuards(
                soft_guards=[{
                    "name": "cvr_warning",
                    "condition": "metrics.cvr_1h >= 0.05",
                    "message": "CVR below optimal"
                }]
            )
        )
        
        result = self.evaluator.evaluate_policies(
            self.sample_context, [policy], [self.sample_action]
        )
        
        assert len(result.allowed) == 1
        assert len(result.blocked) == 0
        assert "CVR below optimal" in result.notes

    def test_rate_limit_enforcement(self):
        """Test rate limiting functionality."""
        policy = RCPPolicy(
            id="test-policy",
            name="Test Policy",
            scope="global",
            mode="enforce",
            enabled=True,
            authority_required="admin",
            limits=RCPLimits(
                rate_limits=[{
                    "name": "actions_per_minute",
                    "limit": 2,
                    "window_minutes": 1,
                    "scope": "global"
                }]
            )
        )
        
        actions = [
            self.sample_action,
            ActionDTO(
                id="action-002",
                type="reweight",
                algo_key="traffic_optimizer",
                idempotency_key="test-key-002",
                data={"target": "destination_456", "weight": 0.7},
                risk_score=1.5
            ),
            ActionDTO(
                id="action-003",
                type="reweight",
                algo_key="traffic_optimizer",
                idempotency_key="test-key-003",
                data={"target": "destination_789", "weight": 0.9},
                risk_score=3.0
            )
        ]
        
        result = self.evaluator.evaluate_policies(
            self.sample_context, [policy], actions
        )
        
        # Should allow first 2 actions, block the 3rd
        assert len(result.allowed) == 2
        assert len(result.blocked) == 1

    def test_risk_limit_enforcement(self):
        """Test risk limit functionality."""
        policy = RCPPolicy(
            id="test-policy",
            name="Test Policy",
            scope="global",
            mode="enforce",
            enabled=True,
            authority_required="admin",
            limits=RCPLimits(
                risk_limits=[{
                    "name": "max_risk_per_action",
                    "limit": 2.0,
                    "message": "Risk too high"
                }]
            )
        )
        
        # Action has risk_score of 2.5, above limit of 2.0
        result = self.evaluator.evaluate_policies(
            self.sample_context, [policy], [self.sample_action]
        )
        
        assert len(result.blocked) == 1
        assert len(result.allowed) == 0
        assert "Risk too high" in result.notes

    def test_weight_mutation_clamp(self):
        """Test weight clamping mutation."""
        policy = RCPPolicy(
            id="test-policy",
            name="Test Policy",
            scope="global",
            mode="enforce",
            enabled=True,
            authority_required="admin",
            mutations=RCPMutations(
                weight_mutations=[{
                    "name": "clamp_weights",
                    "action": "clamp",
                    "field": "weight",
                    "max_value": 0.7,
                    "message": "Weight clamped to maximum"
                }]
            )
        )
        
        result = self.evaluator.evaluate_policies(
            self.sample_context, [policy], [self.sample_action]
        )
        
        assert len(result.modified) == 1
        assert len(result.allowed) == 0
        modified_action = result.modified[0]
        assert modified_action.data["weight"] == 0.7  # Clamped from 0.8

    def test_delta_mutation_limiting(self):
        """Test delta limiting mutation."""
        policy = RCPPolicy(
            id="test-policy",
            name="Test Policy",
            scope="global",
            mode="enforce",
            enabled=True,
            authority_required="admin",
            mutations=RCPMutations(
                delta_mutations=[{
                    "name": "limit_delta",
                    "max_delta_percent": 10,
                    "fields": ["weight"],
                    "message": "Delta limited"
                }]
            )
        )
        
        # Original weight 0.6, new weight 0.8 = 33% increase
        # Should be limited to 10% = 0.66
        result = self.evaluator.evaluate_policies(
            self.sample_context, [policy], [self.sample_action]
        )
        
        assert len(result.modified) == 1
        modified_action = result.modified[0]
        expected_weight = 0.6 * 1.1  # 10% increase
        assert abs(modified_action.data["weight"] - expected_weight) < 0.001

    def test_time_gate_filtering(self):
        """Test time-based gate filtering."""
        # Mock current time to be outside business hours
        with patch('src.soft.rcp.evaluator.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 20, 0)  # 8 PM
            
            policy = RCPPolicy(
                id="test-policy",
                name="Test Policy",
                scope="global",
                mode="enforce",
                enabled=True,
                authority_required="admin",
                gates=RCPGates(
                    time_gates=[{
                        "name": "business_hours",
                        "schedule": "0 9-17 * * 1-5",  # 9 AM to 5 PM, weekdays
                        "timezone": "UTC",
                        "enabled": True
                    }]
                )
            )
            
            # Policy should be filtered out due to time gate
            applicable_policies = self.evaluator._filter_applicable_policies(
                self.sample_context, [policy]
            )
            
            assert len(applicable_policies) == 0

    def test_condition_gate_filtering(self):
        """Test condition-based gate filtering."""
        policy = RCPPolicy(
            id="test-policy",
            name="Test Policy",
            scope="global",
            mode="enforce",
            enabled=True,
            authority_required="admin",
            gates=RCPGates(
                condition_gates=[{
                    "name": "traffic_gate",
                    "condition": "metrics.traffic_volume >= 2000",
                    "message": "Traffic too low"
                }]
            )
        )
        
        # Traffic volume is 1000, below threshold of 2000
        applicable_policies = self.evaluator._filter_applicable_policies(
            self.sample_context, [policy]
        )
        
        assert len(applicable_policies) == 0

    def test_rollout_percentage_filtering(self):
        """Test rollout percentage filtering."""
        policy = RCPPolicy(
            id="test-policy",
            name="Test Policy",
            scope="global",
            mode="enforce",
            enabled=True,
            authority_required="admin",
            rollout=RCPRollout(
                enabled=True,
                percentage=50,
                strategy="random"
            )
        )
        
        # Mock random to return 0.6 (60%) - should be filtered out
        with patch('random.random', return_value=0.6):
            applicable_policies = self.evaluator._filter_applicable_policies(
                self.sample_context, [policy]
            )
            assert len(applicable_policies) == 0
        
        # Mock random to return 0.4 (40%) - should be included
        with patch('random.random', return_value=0.4):
            applicable_policies = self.evaluator._filter_applicable_policies(
                self.sample_context, [policy]
            )
            assert len(applicable_policies) == 1

    def test_algorithm_scope_filtering(self):
        """Test algorithm scope filtering."""
        policy = RCPPolicy(
            id="test-policy",
            name="Test Policy",
            scope="algorithm",
            selector={"algo_key": "different_algorithm"},
            mode="enforce",
            enabled=True,
            authority_required="admin"
        )
        
        # Policy targets different algorithm, should be filtered out
        applicable_policies = self.evaluator._filter_applicable_policies(
            self.sample_context, [policy]
        )
        
        assert len(applicable_policies) == 0

    def test_segment_scope_filtering(self):
        """Test segment scope filtering."""
        policy = RCPPolicy(
            id="test-policy",
            name="Test Policy",
            scope="segment",
            selector={"segment_data.device": "mobile"},
            mode="enforce",
            enabled=True,
            authority_required="admin"
        )
        
        # Context has device=desktop, policy targets mobile
        applicable_policies = self.evaluator._filter_applicable_policies(
            self.sample_context, [policy]
        )
        
        assert len(applicable_policies) == 0

    def test_monitor_mode_no_blocking(self):
        """Test that monitor mode doesn't block actions."""
        policy = RCPPolicy(
            id="test-policy",
            name="Test Policy",
            scope="global",
            mode="monitor",  # Monitor mode
            enabled=True,
            authority_required="admin",
            guards=RCPGuards(
                hard_guards=[{
                    "name": "always_block",
                    "condition": "false",
                    "message": "Would block in enforce mode"
                }]
            )
        )
        
        result = self.evaluator.evaluate_policies(
            self.sample_context, [policy], [self.sample_action]
        )
        
        # In monitor mode, actions are allowed even if guards fail
        assert len(result.allowed) == 1
        assert len(result.blocked) == 0
        assert "Would block in enforce mode" in result.notes

    def test_risk_scoring_heuristics(self):
        """Test risk scoring heuristics."""
        # Test different action types
        reweight_action = ActionDTO(
            id="reweight-001",
            type="reweight",
            algo_key="test",
            idempotency_key="key-001",
            data={"weight": 0.8},
            risk_score=0.0
        )
        
        bid_action = ActionDTO(
            id="bid-001",
            type="bid_adjustment",
            algo_key="test",
            idempotency_key="key-002",
            data={"bid": 1.5},
            risk_score=0.0
        )
        
        # Apply risk scoring
        reweight_risk = self.evaluator._calculate_risk_score(reweight_action)
        bid_risk = self.evaluator._calculate_risk_score(bid_action)
        
        # Bid adjustments should have higher base risk
        assert bid_risk > reweight_risk

    def test_complex_policy_evaluation(self):
        """Test evaluation with multiple policy components."""
        policy = RCPPolicy(
            id="complex-policy",
            name="Complex Policy",
            scope="global",
            mode="enforce",
            enabled=True,
            authority_required="admin",
            guards=RCPGuards(
                soft_guards=[{
                    "name": "performance_warning",
                    "condition": "metrics.cvr_1h >= 0.04",
                    "message": "Performance below optimal"
                }]
            ),
            limits=RCPLimits(
                risk_limits=[{
                    "name": "risk_limit",
                    "limit": 5.0,
                    "message": "Risk acceptable"
                }]
            ),
            mutations=RCPMutations(
                weight_mutations=[{
                    "name": "conservative_scaling",
                    "condition": "metrics.cvr_1h < 0.05",
                    "action": "multiply",
                    "field": "weight",
                    "factor": 0.9,
                    "message": "Conservative scaling applied"
                }]
            )
        )
        
        result = self.evaluator.evaluate_policies(
            self.sample_context, [policy], [self.sample_action]
        )
        
        # Should be modified (mutation applied) and generate warning
        assert len(result.modified) == 1
        assert len(result.blocked) == 0
        assert "Performance below optimal" in result.notes
        assert "Conservative scaling applied" in result.notes
        
        modified_action = result.modified[0]
        expected_weight = 0.8 * 0.9  # 90% scaling
        assert abs(modified_action.data["weight"] - expected_weight) < 0.001

    def test_evaluation_statistics(self):
        """Test evaluation statistics calculation."""
        policies = [
            RCPPolicy(
                id="policy-1",
                name="Policy 1",
                scope="global",
                mode="enforce",
                enabled=True,
                authority_required="admin",
                guards=RCPGuards(
                    hard_guards=[{
                        "name": "block_high_risk",
                        "condition": "action.risk_score <= 2.0",
                        "message": "Risk too high"
                    }]
                )
            )
        ]
        
        actions = [
            ActionDTO(
                id="low-risk",
                type="reweight",
                algo_key="test",
                idempotency_key="key-1",
                data={"weight": 0.7},
                risk_score=1.5
            ),
            ActionDTO(
                id="high-risk",
                type="reweight",
                algo_key="test",
                idempotency_key="key-2",
                data={"weight": 0.9},
                risk_score=3.0
            )
        ]
        
        result = self.evaluator.evaluate_policies(
            self.sample_context, policies, actions
        )
        
        assert len(result.allowed) == 1
        assert len(result.blocked) == 1
        assert result.risk_cost > 0
        assert len(result.notes) > 0
