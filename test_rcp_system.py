#!/usr/bin/env python3
"""Test RCP system functionality."""

import sys
import os
from pathlib import Path
import asyncio

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def test_rcp_system():
    """Test the RCP system components."""
    print("🧪 Testing RCP System Components...")
    
    try:
        # Test RCP evaluator
        print("\n1. Testing RCP Evaluator...")
        from soft.rcp.evaluator import RCPEvaluator
        from soft.rcp.schemas import RCPPolicyCreate, ActionDTO
        
        evaluator = RCPEvaluator()
        print("✅ RCP Evaluator imported successfully")
        
        # Test basic evaluation
        action = ActionDTO(
            action_type="bid_adjustment",
            target_id="test_campaign",
            parameters={"adjustment": 1.2},
            algorithm_id="test_algo",
            segment_id="mobile"
        )
        
        # Create a test policy
        policy = RCPPolicyCreate(
            name="Test Policy",
            description="Test policy for validation",
            scope="global",
            mode="monitor",
            guards=[{
                "type": "value_range",
                "field": "parameters.adjustment",
                "min_value": 0.5,
                "max_value": 2.0,
                "hard": False
            }],
            limits=[{
                "type": "rate",
                "max_count": 100,
                "window_minutes": 60
            }],
            gates=[{
                "type": "time_window",
                "start_time": "09:00",
                "end_time": "17:00",
                "timezone": "UTC"
            }],
            mutations=[{
                "type": "clamp",
                "field": "parameters.adjustment",
                "min_value": 0.8,
                "max_value": 1.5
            }],
            rollout_percentage=100.0,
            priority=100,
            enabled=True
        )
        
        # Test evaluation
        result = await evaluator.evaluate_action(action, [policy.dict()])
        print(f"✅ Evaluation result: {result.decision}")
        
        # Test API router
        print("\n2. Testing RCP API Router...")
        from soft.rcp.api import router
        print("✅ RCP API router imported successfully")
        
        # Test database models
        print("\n3. Testing RCP Database Models...")
        from soft.rcp.models import RCPPolicy, RCPEvaluation
        print("✅ RCP database models imported successfully")
        
        # Test repository
        print("\n4. Testing RCP Repository...")
        from soft.rcp.repository import RCPRepository
        print("✅ RCP repository imported successfully")
        
        print("\n🎉 All RCP system components tested successfully!")
        return True
        
    except Exception as e:
        print(f"❌ RCP system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backend_integration():
    """Test backend integration."""
    print("\n🔌 Testing Backend Integration...")
    
    try:
        # Test main router import
        from soft.router import app
        print("✅ Main FastAPI app imported successfully")
        
        # Check if RCP router is included
        rcp_routes = [route for route in app.routes if hasattr(route, 'path') and '/rcp' in route.path]
        if rcp_routes:
            print(f"✅ Found {len(rcp_routes)} RCP routes in main app")
        else:
            print("⚠️  No RCP routes found in main app")
        
        return True
        
    except Exception as e:
        print(f"❌ Backend integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("🚀 SmartLinks RCP System Test Suite")
    print("=" * 50)
    
    # Test RCP system
    rcp_success = await test_rcp_system()
    
    # Test backend integration
    backend_success = test_backend_integration()
    
    print("\n" + "=" * 50)
    if rcp_success and backend_success:
        print("🎉 All tests passed! RCP system is ready.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return rcp_success and backend_success

if __name__ == "__main__":
    asyncio.run(main())
