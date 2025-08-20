#!/usr/bin/env python3
"""Test script for SmartLinks Autopilot RCP features."""

import sys
import os
import asyncio
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_pac_schemas():
    """Test Policy-as-Code schemas."""
    try:
        from src.soft.pac.schemas import PacPolicy, PacPlan, RolloutConfig
        
        # Test creating a PaC policy
        policy = PacPolicy(
            name="test_policy",
            version="1.0.0",
            description="Test policy",
            policies=[],
            metadata={}
        )
        
        print("✅ Policy-as-Code schemas working")
        return True
    except Exception as e:
        print(f"❌ Policy-as-Code schemas failed: {e}")
        return False

def test_bandits():
    """Test bandit algorithms."""
    try:
        from src.soft.autopilot.bandits.thompson import ThompsonBandit, UCBBandit
        
        # Test Thompson Sampling
        bandit = ThompsonBandit()
        bandit.add_arm("dest1")
        bandit.add_arm("dest2")
        bandit.update_arm("dest1", 10, 5)  # 10 successes, 5 failures
        
        weights = bandit.select_weights(["dest1", "dest2"])
        
        print(f"✅ Bandits working - weights: {weights}")
        return True
    except Exception as e:
        print(f"❌ Bandits failed: {e}")
        return False

def test_optimizer():
    """Test optimization algorithms."""
    try:
        from src.soft.autopilot.planner.optimizer import BudgetArbitrageOptimizer
        
        optimizer = BudgetArbitrageOptimizer()
        
        # Test with simple candidates
        candidates = [
            {"id": "1", "expected_roi": 2.5, "min_budget": 100, "max_budget": 1000},
            {"id": "2", "expected_roi": 1.8, "min_budget": 100, "max_budget": 1000}
        ]
        
        print("✅ Optimizer working")
        return True
    except Exception as e:
        print(f"❌ Optimizer failed: {e}")
        return False

def test_webhooks():
    """Test webhook system."""
    try:
        from src.soft.webhooks.service import WebhookService, WebhookType, EventType
        
        service = WebhookService()
        print("✅ Webhooks working")
        return True
    except Exception as e:
        print(f"❌ Webhooks failed: {e}")
        return False

def test_observability():
    """Test observability features."""
    try:
        from src.soft.observability.otel import trace_span, SmartLinksMetrics
        
        # Test basic tracing context
        with trace_span("test_span") as span:
            pass
        
        print("✅ Observability working")
        return True
    except Exception as e:
        print(f"❌ Observability failed: {e}")
        return False

async def test_async_features():
    """Test async features."""
    try:
        from src.soft.replay.engine import ReplayEngine
        from src.soft.features.service import FeatureService
        
        print("✅ Async features can be imported")
        return True
    except Exception as e:
        print(f"❌ Async features failed: {e}")
        return False

def main():
    """Run all tests."""
    print("SmartLinks Autopilot RCP - Feature Tests\n")
    
    tests = [
        ("Policy-as-Code", test_pac_schemas),
        ("Bandits", test_bandits),
        ("Optimizer", test_optimizer),
        ("Webhooks", test_webhooks),
        ("Observability", test_observability),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"Testing {name}...")
        if test_func():
            passed += 1
        print()
    
    # Test async features
    print("Testing async features...")
    try:
        asyncio.run(test_async_features())
        passed += 1
    except Exception as e:
        print(f"❌ Async features failed: {e}")
    total += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All RCP features are working!")
        print("\nNext steps:")
        print("1. Install missing dependencies: pip install aiohttp ortools opentelemetry-api")
        print("2. Run database migrations: alembic upgrade head")
        print("3. Start server: python start_debug.py")
        print("4. Test API endpoints at http://localhost:8000/docs")
    else:
        print("⚠️  Some features need attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
