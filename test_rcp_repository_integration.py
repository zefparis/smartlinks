#!/usr/bin/env python3
"""Test script to verify RCP repository integration with AlgorithmRun model."""

import uuid
from datetime import datetime
from src.soft.rcp.repository import RCPRepository
from src.soft.rcp.models import RCPPolicy, RCPEvaluation
from src.soft.autopilot.models import AlgorithmRun
from src.backend.database import get_db

def test_rcp_repository_integration():
    """Test RCP repository integration with AlgorithmRun model."""
    print("🧪 Testing RCP repository integration with AlgorithmRun model...")
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    # Create RCP repository instance
    rcp_repo = RCPRepository(db)
    
    # Create a test AlgorithmRun record
    run_id = str(uuid.uuid4())
    algo_key = "test_algorithm"
    
    run_record = AlgorithmRun(
        id=run_id,
        algo_key=algo_key,
        status="started"
    )
    
    db.add(run_record)
    db.commit()
    
    print(f"✅ Created AlgorithmRun record with ID: {run_id}")
    
    # Create a test RCP policy
    policy_id = str(uuid.uuid4())
    policy = RCPPolicy(
        id=policy_id,
        name="Test Policy",
        scope="algorithm",
        algo_key=algo_key,
        mode="active",
        authority_required="advisory",
        hard_guards_json={"max_actions": 10},
        soft_guards_json={"max_risk": 5},
        limits_json={"daily_budget": 100},
        gates_json=[],
        mutations_json=[],
        schedule_cron="* * * * *",
        rollout_percent=100.0,
        enabled=True
    )
    
    db.add(policy)
    db.commit()
    
    print(f"✅ Created RCP policy with ID: {policy_id}")
    
    # Create an RCP evaluation record linked to the AlgorithmRun
    stats = {
        "risk_cost": 3,
        "actions_allowed": 5,
        "actions_modified": 5,
        "actions_blocked": 0,
        "evaluation_time_ms": 10.5,
        "policies_applied": 1
    }
    
    diff = {
        "before": ["action1", "action2", "action3"],
        "after": ["action1", "action2", "action3"],
        "changes": []
    }
    
    evaluation = rcp_repo.create_evaluation(
        policy_id=policy_id,
        algo_key=algo_key,
        run_id=run_id,
        result="allowed",
        stats=stats,
        diff=diff
    )
    
    print(f"✅ Created RCPEvaluation record with ID: {evaluation.id}")
    
    # Retrieve the evaluation record
    retrieved_evaluation = db.query(RCPEvaluation).filter(
        RCPEvaluation.id == evaluation.id
    ).first()
    
    if retrieved_evaluation:
        print(f"✅ Retrieved RCPEvaluation record: {retrieved_evaluation.id}")
        print(f"   Policy ID: {retrieved_evaluation.policy_id}")
        print(f"   Algorithm Key: {retrieved_evaluation.algo_key}")
        print(f"   Run ID: {retrieved_evaluation.run_id}")
        print(f"   Result: {retrieved_evaluation.result}")
    else:
        print("❌ Failed to retrieve RCPEvaluation record")
        return False
    
    # Verify that the evaluation is properly linked to the AlgorithmRun
    if retrieved_evaluation.run_id == run_id:
        print("✅ RCPEvaluation properly linked to AlgorithmRun")
    else:
        print("❌ RCPEvaluation not properly linked to AlgorithmRun")
        return False
    
    # Update the AlgorithmRun record
    run_record.status = "completed"
    run_record.completed_at = datetime.now()
    run_record.settings_version = 1
    run_record.ai_authority_used = "full_control"
    run_record.risk_cost = 3
    run_record.rcp_applied = True
    
    db.commit()
    
    print("✅ Updated AlgorithmRun record with RCP data")
    
    # Retrieve the updated AlgorithmRun record
    updated_run_record = db.query(AlgorithmRun).filter(
        AlgorithmRun.id == run_id
    ).first()
    
    if updated_run_record:
        print(f"✅ Retrieved updated AlgorithmRun record: {updated_run_record.status}")
        print(f"   RCP Applied: {updated_run_record.rcp_applied}")
        print(f"   Risk Cost: {updated_run_record.risk_cost}")
    else:
        print("❌ Failed to retrieve updated AlgorithmRun record")
        return False
    
    return True

if __name__ == "__main__":
    success = test_rcp_repository_integration()
    if success:
        print("\n🎉 RCP repository integration test passed!")
    else:
        print("\n💥 RCP repository integration test failed!")
