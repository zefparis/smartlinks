"""Test AlgorithmRunner integration with AlgorithmRun model."""

import pytest
import asyncio
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from src.soft.autopilot.models import AlgorithmRun
from src.soft.autopilot.runner import AlgorithmRunner
from src.backend.database import get_db


class TestAlgorithmRunnerIntegration:
    """Test AlgorithmRunner integration with AlgorithmRun model."""
    
    @pytest.fixture
    def runner(self):
        """Create an AlgorithmRunner instance."""
        # Get database session factory
        def get_db_session_factory():
            db_gen = get_db()
            db = next(db_gen)
            return lambda: db
        
        return AlgorithmRunner(get_db_session_factory())
    
    def test_run_algorithm_creates_run_record(self, runner):
        """Test that running an algorithm creates a run record."""
        algo_key = "traffic_optimizer"
        
        # Run the algorithm
        result = asyncio.run(runner.run_algorithm(algo_key))
        
        # Check that the result contains a run_id
        assert "run_id" in result
        run_id = result["run_id"]
        
        # Get database session to check record
        db_gen = get_db()
        db_session = next(db_gen)
        
        # Retrieve the run record from the database
        run_record = db_session.query(AlgorithmRun).filter(
            AlgorithmRun.id == run_id
        ).first()
        
        assert run_record is not None
        assert run_record.algo_key == algo_key
        assert run_record.status in ["completed", "inactive", "error"]
        assert run_record.started_at is not None
        
    def test_run_algorithm_updates_run_record(self, runner):
        """Test that running an algorithm updates the run record."""
        algo_key = "traffic_optimizer"
        
        # Run the algorithm
        result = asyncio.run(runner.run_algorithm(algo_key))
        
        # Check that the result contains a run_id
        assert "run_id" in result
        run_id = result["run_id"]
        
        # Get database session to check record
        db_gen = get_db()
        db_session = next(db_gen)
        
        # Retrieve the run record from the database
        run_record = db_session.query(AlgorithmRun).filter(
            AlgorithmRun.id == run_id
        ).first()
        
        # Verify that the run record was updated properly
        assert run_record.status == "completed"
        assert run_record.completed_at is not None
        assert run_record.settings_version is not None
        assert run_record.ai_authority_used is not None
        assert run_record.rcp_applied is not None
