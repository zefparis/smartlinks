#!/usr/bin/env python3
"""Comprehensive test of RCP integration with AlgorithmRun model."""

import asyncio
import uuid
from datetime import datetime
from src.soft.autopilot.models import AlgorithmRun
from src.soft.autopilot.runner import AlgorithmRunner
from src.backend.database import get_db

def test_complete_rcp_integration():
    """Test complete RCP integration including AlgorithmRun model."""
    print("🧪 Testing complete RCP integration...")
    
    # Get database session factory
    def get_db_session_factory():
        db_gen = get_db()
        db = next(db_gen)
        return lambda: db
    
    # Create AlgorithmRunner instance
    runner = AlgorithmRunner(get_db_session_factory())
    
    # Run an algorithm
    print("🔄 Running traffic_optimizer algorithm...")
    result = asyncio.run(runner.run_algorithm("traffic_optimizer"))
    
    print(f"✅ Algorithm run completed with result: {result}")
    
    # Check that result contains required fields
    required_fields = ["status", "run_id", "executed_actions", "failed_actions", "total_risk_used", "rcp_applied", "rcp_risk_cost"]
    for field in required_fields:
        if field in result:
            print(f"   {field}: {result[field]}")
        else:
            print(f"❌ Missing required field: {field}")
            return False
    
    # Get database session to check AlgorithmRun record
    db_gen = get_db()
    db = next(db_gen)
    
    # Retrieve the run record from the database
    run_id = result["run_id"]
    run_record = db.query(AlgorithmRun).filter(
        AlgorithmRun.id == run_id
    ).first()
    
    if run_record:
        print(f"✅ Found AlgorithmRun record in database: {run_record.id}")
        print(f"   algo_key: {run_record.algo_key}")
        print(f"   status: {run_record.status}")
        print(f"   started_at: {run_record.started_at}")
        print(f"   completed_at: {run_record.completed_at}")
        print(f"   settings_version: {run_record.settings_version}")
        print(f"   ai_authority_used: {run_record.ai_authority_used}")
        print(f"   risk_cost: {run_record.risk_cost}")
        print(f"   rcp_applied: {run_record.rcp_applied}")
    else:
        print("❌ Failed to find AlgorithmRun record in database")
        return False
    
    # Verify that the run record was properly updated
    if run_record.status != "completed":
        print(f"❌ AlgorithmRun status should be 'completed' but is '{run_record.status}'")
        return False
    
    if run_record.completed_at is None:
        print("❌ AlgorithmRun completed_at should not be None")
        return False
    
    if run_record.settings_version is None:
        print("❌ AlgorithmRun settings_version should not be None")
        return False
    
    if run_record.ai_authority_used is None:
        print("❌ AlgorithmRun ai_authority_used should not be None")
        return False
    
    if run_record.rcp_applied is None:
        print("❌ AlgorithmRun rcp_applied should not be None")
        return False
    
    print("✅ All AlgorithmRun record fields properly updated")
    return True

if __name__ == "__main__":
    success = test_complete_rcp_integration()
    if success:
        print("\n🎉 Complete RCP integration test passed!")
    else:
        print("\n💥 Complete RCP integration test failed!")
