"""Test AlgorithmRun model and AlgorithmRunner integration."""

import pytest
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from src.soft.autopilot.models import AlgorithmRun
from src.backend.database import get_db


class TestAlgorithmRun:
    """Test AlgorithmRun model functionality."""
    
    def test_algorithm_run_creation(self):
        """Test creating an algorithm run record."""
        # Get database session
        db_gen = get_db()
        db_session = next(db_gen)
        
        run_id = str(uuid.uuid4())
        algo_key = "test_algorithm"
        
        # Create a new algorithm run record
        run_record = AlgorithmRun(
            id=run_id,
            algo_key=algo_key,
            status="started"
        )
        
        db_session.add(run_record)
        db_session.commit()
        
        # Retrieve the record
        retrieved_record = db_session.query(AlgorithmRun).filter(
            AlgorithmRun.id == run_id
        ).first()
        
        assert retrieved_record is not None
        assert retrieved_record.id == run_id
        assert retrieved_record.algo_key == algo_key
        assert retrieved_record.status == "started"
        assert retrieved_record.started_at is not None
        assert retrieved_record.completed_at is None
        assert retrieved_record.settings_version is None
        assert retrieved_record.ai_authority_used is None
        assert retrieved_record.risk_cost is None
        assert retrieved_record.rcp_applied == False
        assert retrieved_record.error_message is None
    
    def test_algorithm_run_update(self):
        """Test updating an algorithm run record."""
        # Get database session
        db_gen = get_db()
        db_session = next(db_gen)
        
        run_id = str(uuid.uuid4())
        algo_key = "test_algorithm"
        
        # Create a new algorithm run record
        run_record = AlgorithmRun(
            id=run_id,
            algo_key=algo_key,
            status="started"
        )
        
        db_session.add(run_record)
        db_session.commit()
        
        # Update the record
        run_record.status = "completed"
        run_record.completed_at = datetime.now()
        run_record.settings_version = 1
        run_record.ai_authority_used = "full_control"
        run_record.risk_cost = 5
        run_record.rcp_applied = True
        run_record.error_message = None
        
        db_session.commit()
        
        # Retrieve the updated record
        retrieved_record = db_session.query(AlgorithmRun).filter(
            AlgorithmRun.id == run_id
        ).first()
        
        assert retrieved_record.status == "completed"
        assert retrieved_record.completed_at is not None
        assert retrieved_record.settings_version == 1
        assert retrieved_record.ai_authority_used == "full_control"
        assert retrieved_record.risk_cost == 5
        assert retrieved_record.rcp_applied == True
        assert retrieved_record.error_message is None
