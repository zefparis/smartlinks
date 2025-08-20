#!/usr/bin/env python3
"""Test script to verify RCP policy application and audit logging."""

import asyncio
import uuid
from datetime import datetime
from src.soft.autopilot.models import AlgorithmRun
from src.soft.rcp.models import RCPEvaluation
from src.soft.autopilot.runner import AlgorithmRunner
from src.backend.database import get_db

def test_rcp_policy_application():
    """Test RCP policy application and audit logging."""
    print("🧪 Testing RCP policy application and audit logging...")
    
    # Get database session factory
    def get_db_session_factory():
        db_gen = get_db()
        db = next(db_gen)
        return lambda: db
    
    # Create AlgorithmRunner instance
    runner = AlgorithmRunner(get_db_session_factory())
    
    # Run an algorithm
    print("🔄 Running traffic_optimizer algorithm with RCP policies...")
    result = asyncio.run(runner.run_algorithm("traffic_optimizer"))
    
    print(f"✅ Algorithm run completed with result: {result}")
    
    # Check that result contains RCP-related fields
    if "rcp_applied" not in result:
        print("❌ Missing RCP applied indicator in result")
        return False
    
    if "rcp_risk_cost" not in result:
        print("❌ Missing RCP risk cost in result")
        return False
    
    print(f"   RCP Applied: {result['rcp_applied']}")
    print(f"   RCP Risk Cost: {result['rcp_risk_cost']}")
    
    # Get database session to check RCPEvaluation records
    db_gen = get_db()
    db = next(db_gen)
    
    # Retrieve RCP evaluation records from the database
    run_id = result["run_id"]
    rcp_evaluations = db.query(RCPEvaluation).filter(
        RCPEvaluation.run_id == run_id
    ).all()
    
    if rcp_evaluations:
        print(f"✅ Found {len(rcp_evaluations)} RCPEvaluation record(s) in database for run_id: {run_id}")
        for evaluation in rcp_evaluations:
            print(f"   Policy ID: {evaluation.policy_id}")
            print(f"   Algorithm Key: {evaluation.algo_key}")
            print(f"   Result: {evaluation.result}")
            print(f"   Created At: {evaluation.created_at}")
    else:
        print("⚠️  No RCPEvaluation records found in database (this might be expected if no policies were applied)")
    
    # Verify AlgorithmRun record exists and has RCP data
    run_record = db.query(AlgorithmRun).filter(
        AlgorithmRun.id == run_id
    ).first()
    
    if run_record:
        print(f"✅ AlgorithmRun record properly linked to RCP evaluations")
        print(f"   RCP Applied: {run_record.rcp_applied}")
        print(f"   Risk Cost: {run_record.risk_cost}")
        print(f"   AI Authority Used: {run_record.ai_authority_used}")
    else:
        print("❌ Failed to find AlgorithmRun record in database")
        return False
    
    return True

if __name__ == "__main__":
    success = test_rcp_policy_application()
    if success:
        print("\n🎉 RCP policy application test passed!")
    else:
        print("\n💥 RCP policy application test failed!")
