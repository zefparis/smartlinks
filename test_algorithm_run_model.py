#!/usr/bin/env python3
"""Test script to verify AlgorithmRun model works correctly with the database."""

import uuid
from datetime import datetime
from src.soft.autopilot.models import AlgorithmRun
from src.backend.database import get_db

def test_algorithm_run_model():
    """Test AlgorithmRun model creation and retrieval."""
    print("🧪 Testing AlgorithmRun model...")
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    # Create a new algorithm run record
    run_id = str(uuid.uuid4())
    algo_key = "test_algorithm"
    
    run_record = AlgorithmRun(
        id=run_id,
        algo_key=algo_key,
        status="started"
    )
    
    # Add and commit to database
    db.add(run_record)
    db.commit()
    
    print(f"✅ Created AlgorithmRun record with ID: {run_id}")
    
    # Retrieve the record
    retrieved_record = db.query(AlgorithmRun).filter(
        AlgorithmRun.id == run_id
    ).first()
    
    if retrieved_record:
        print(f"✅ Retrieved AlgorithmRun record: {retrieved_record.id}")
        print(f"   algo_key: {retrieved_record.algo_key}")
        print(f"   status: {retrieved_record.status}")
        print(f"   started_at: {retrieved_record.started_at}")
    else:
        print("❌ Failed to retrieve AlgorithmRun record")
        return False
    
    # Update the record
    retrieved_record.status = "completed"
    retrieved_record.completed_at = datetime.now()
    retrieved_record.settings_version = 1
    retrieved_record.ai_authority_used = "full_control"
    retrieved_record.risk_cost = 5
    retrieved_record.rcp_applied = True
    
    db.commit()
    
    print("✅ Updated AlgorithmRun record")
    
    # Retrieve the updated record
    updated_record = db.query(AlgorithmRun).filter(
        AlgorithmRun.id == run_id
    ).first()
    
    if updated_record:
        print(f"✅ Retrieved updated AlgorithmRun record: {updated_record.status}")
        print(f"   completed_at: {updated_record.completed_at}")
        print(f"   settings_version: {updated_record.settings_version}")
        print(f"   ai_authority_used: {updated_record.ai_authority_used}")
        print(f"   risk_cost: {updated_record.risk_cost}")
        print(f"   rcp_applied: {updated_record.rcp_applied}")
    else:
        print("❌ Failed to retrieve updated AlgorithmRun record")
        return False
    
    return True

if __name__ == "__main__":
    success = test_algorithm_run_model()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Some tests failed!")
