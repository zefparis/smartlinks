"""
Tests for RCP API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime
from src.soft.rcp.api import router
from src.soft.rcp.schemas import RCPPolicyCreate, RCPPreviewRequest
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestRCPAPI:
    
    def setup_method(self):
        """Setup test fixtures."""
        self.headers = {"X-Role": "admin"}
        
        self.sample_policy = {
            "id": "test-policy-001",
            "name": "Test Policy",
            "description": "Test policy for API testing",
            "scope": "global",
            "mode": "enforce",
            "enabled": True,
            "authority_required": "admin",
            "guards": {
                "hard_guards": [{
                    "name": "test_guard",
                    "condition": "metrics.cvr_1h >= 0.02",
                    "message": "CVR too low"
                }]
            },
            "limits": {},
            "gates": {},
            "mutations": {},
            "scheduling": {"enabled": False},
            "rollout": {"enabled": True, "percentage": 100, "strategy": "random"},
            "metadata": {"test": True}
        }

    @patch('src.soft.rcp.api.get_db')
    @patch('src.soft.rcp.api.RCPRepository')
    def test_list_policies_success(self, mock_repo_class, mock_get_db):
        """Test successful policy listing."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.list_policies.return_value = []
        
        response = client.get("/rcp/policies", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "policies" in data
        assert "total" in data

    def test_list_policies_insufficient_permissions(self):
        """Test policy listing with insufficient permissions."""
        headers = {"X-Role": "viewer"}
        
        response = client.get("/rcp/policies", headers=headers)
        
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    @patch('src.soft.rcp.api.get_db')
    @patch('src.soft.rcp.api.RCPRepository')
    def test_create_policy_success(self, mock_repo_class, mock_get_db):
        """Test successful policy creation."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_policy.return_value = None  # Policy doesn't exist
        mock_repo.create_policy.return_value = Mock(id="test-policy-001")
        
        response = client.post(
            "/rcp/policies",
            json=self.sample_policy,
            headers=self.headers
        )
        
        assert response.status_code == 200
        mock_repo.create_policy.assert_called_once()

    @patch('src.soft.rcp.api.get_db')
    @patch('src.soft.rcp.api.RCPRepository')
    def test_create_policy_already_exists(self, mock_repo_class, mock_get_db):
        """Test policy creation when policy already exists."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_policy.return_value = Mock()  # Policy exists
        
        response = client.post(
            "/rcp/policies",
            json=self.sample_policy,
            headers=self.headers
        )
        
        assert response.status_code == 409
        assert "Policy already exists" in response.json()["detail"]

    def test_create_policy_insufficient_permissions(self):
        """Test policy creation with insufficient permissions."""
        headers = {"X-Role": "viewer"}
        
        response = client.post(
            "/rcp/policies",
            json=self.sample_policy,
            headers=headers
        )
        
        assert response.status_code == 403

    @patch('src.soft.rcp.api.get_db')
    @patch('src.soft.rcp.api.RCPRepository')
    def test_get_policy_success(self, mock_repo_class, mock_get_db):
        """Test successful policy retrieval."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_policy = Mock()
        mock_policy.id = "test-policy-001"
        mock_repo.get_policy.return_value = mock_policy
        
        response = client.get("/rcp/policies/test-policy-001", headers=self.headers)
        
        assert response.status_code == 200

    @patch('src.soft.rcp.api.get_db')
    @patch('src.soft.rcp.api.RCPRepository')
    def test_get_policy_not_found(self, mock_repo_class, mock_get_db):
        """Test policy retrieval when policy doesn't exist."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_policy.return_value = None
        
        response = client.get("/rcp/policies/nonexistent", headers=self.headers)
        
        assert response.status_code == 404

    @patch('src.soft.rcp.api.get_db')
    @patch('src.soft.rcp.api.RCPRepository')
    def test_update_policy_success(self, mock_repo_class, mock_get_db):
        """Test successful policy update."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_policy = Mock()
        mock_repo.update_policy.return_value = mock_policy
        
        update_data = {"enabled": False, "description": "Updated description"}
        
        response = client.put(
            "/rcp/policies/test-policy-001",
            json=update_data,
            headers=self.headers
        )
        
        assert response.status_code == 200

    @patch('src.soft.rcp.api.get_db')
    @patch('src.soft.rcp.api.RCPRepository')
    def test_delete_policy_success(self, mock_repo_class, mock_get_db):
        """Test successful policy deletion."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.delete_policy.return_value = True
        
        response = client.delete("/rcp/policies/test-policy-001", headers=self.headers)
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

    @patch('src.soft.rcp.api.get_db')
    @patch('src.soft.rcp.api.RCPRepository')
    def test_delete_policy_not_found(self, mock_repo_class, mock_get_db):
        """Test policy deletion when policy doesn't exist."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.delete_policy.return_value = False
        
        response = client.delete("/rcp/policies/nonexistent", headers=self.headers)
        
        assert response.status_code == 404

    @patch('src.soft.rcp.api.get_db')
    @patch('src.soft.rcp.api.RCPRepository')
    @patch('src.soft.rcp.api.RCPEvaluator')
    def test_preview_evaluation_success(self, mock_evaluator_class, mock_repo_class, mock_get_db):
        """Test successful RCP preview evaluation."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_applicable_policies.return_value = []
        
        mock_evaluator = Mock()
        mock_evaluator_class.return_value = mock_evaluator
        mock_result = Mock()
        mock_result.allowed = []
        mock_result.modified = []
        mock_result.blocked = []
        mock_result.risk_cost = 0.0
        mock_result.notes = []
        mock_evaluator.evaluate_policies.return_value = mock_result
        
        preview_data = {
            "algo_key": "traffic_optimizer",
            "actions": [{
                "id": "action-001",
                "type": "reweight",
                "algo_key": "traffic_optimizer",
                "idempotency_key": "key-001",
                "data": {"weight": 0.8},
                "risk_score": 2.5
            }],
            "ctx": {
                "metrics": {"cvr_1h": 0.045},
                "segment_data": {"device": "desktop"}
            }
        }
        
        response = client.post(
            "/rcp/preview",
            json=preview_data,
            headers=self.headers
        )
        
        assert response.status_code == 200

    @patch('src.soft.rcp.api.get_db')
    @patch('src.soft.rcp.api.RCPRepository')
    def test_list_evaluations_success(self, mock_repo_class, mock_get_db):
        """Test successful evaluation listing."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.list_evaluations.return_value = []
        
        response = client.get("/rcp/evaluations", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "evaluations" in data
        assert "total" in data

    @patch('src.soft.rcp.api.get_db')
    @patch('src.soft.rcp.api.RCPRepository')
    def test_get_evaluation_stats_success(self, mock_repo_class, mock_get_db):
        """Test successful evaluation statistics retrieval."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_evaluation_stats.return_value = {
            "total_evaluations": 100,
            "blocked_actions": 5,
            "modified_actions": 15
        }
        
        response = client.get("/rcp/evaluations/stats", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_evaluations" in data

    @patch('src.soft.rcp.api.get_db')
    @patch('src.soft.rcp.api.RCPRepository')
    def test_check_policy_applicable_success(self, mock_repo_class, mock_get_db):
        """Test successful policy applicability check."""
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_policy = Mock()
        mock_policy.id = "test-policy-001"
        mock_repo.get_policy.return_value = mock_policy
        mock_repo.get_applicable_policies.return_value = [mock_policy]
        
        response = client.get(
            "/rcp/policies/test-policy-001/applicable?algo_key=traffic_optimizer",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["applicable"] is True

    def test_rbac_enforcement(self):
        """Test RBAC enforcement across endpoints."""
        # Test with no role header
        response = client.get("/rcp/policies")
        assert response.status_code == 403
        
        # Test with viewer role (read-only)
        viewer_headers = {"X-Role": "viewer"}
        response = client.get("/rcp/policies", headers=viewer_headers)
        assert response.status_code == 200
        
        # Test viewer trying to create policy
        response = client.post("/rcp/policies", json=self.sample_policy, headers=viewer_headers)
        assert response.status_code == 403

    def test_input_validation(self):
        """Test input validation for API endpoints."""
        # Test invalid policy data
        invalid_policy = {
            "id": "",  # Empty ID
            "scope": "invalid_scope",  # Invalid scope
            "mode": "invalid_mode"  # Invalid mode
        }
        
        response = client.post(
            "/rcp/policies",
            json=invalid_policy,
            headers=self.headers
        )
        
        assert response.status_code == 422  # Validation error

    def test_pagination_parameters(self):
        """Test pagination parameter validation."""
        # Test invalid page number
        response = client.get("/rcp/policies?page=0", headers=self.headers)
        assert response.status_code == 422
        
        # Test invalid per_page number
        response = client.get("/rcp/policies?per_page=101", headers=self.headers)
        assert response.status_code == 422
