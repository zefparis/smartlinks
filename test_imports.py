#!/usr/bin/env python3
"""Test script to verify all new RCP features can be imported."""

import sys
import traceback

def test_import(module_name, description):
    """Test importing a module."""
    try:
        __import__(module_name)
        print(f"✅ {description}: OK")
        return True
    except ImportError as e:
        print(f"❌ {description}: FAILED - {e}")
        return False
    except Exception as e:
        print(f"❌ {description}: ERROR - {e}")
        return False

def main():
    """Test all imports."""
    print("Testing SmartLinks Autopilot RCP imports...\n")
    
    # Test core dependencies
    tests = [
        ("aiohttp", "aiohttp HTTP client"),
        ("redis", "Redis client"),
        ("ortools", "OR-Tools optimization"),
        ("opentelemetry", "OpenTelemetry observability"),
        ("yaml", "YAML parser"),
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
    ]
    
    success_count = 0
    for module, desc in tests:
        if test_import(module, desc):
            success_count += 1
    
    print(f"\nCore dependencies: {success_count}/{len(tests)} OK\n")
    
    # Test new RCP modules
    rcp_tests = [
        ("src.soft.pac.models", "Policy-as-Code models"),
        ("src.soft.pac.schemas", "Policy-as-Code schemas"),
        ("src.soft.pac.loader", "Policy-as-Code loader"),
        ("src.soft.pac.service", "Policy-as-Code service"),
        ("src.soft.pac.api", "Policy-as-Code API"),
        ("src.soft.replay.engine", "Replay & Decision Graph engine"),
        ("src.soft.replay.api", "Replay API"),
        ("src.soft.features.service", "Feature Store service"),
        ("src.soft.features.api", "Feature Store API"),
        ("src.soft.autopilot.bandits.thompson", "Thompson Sampling bandits"),
        ("src.soft.autopilot.planner.optimizer", "Budget optimizer"),
        ("src.soft.backtesting.engine", "Backtesting engine"),
        ("src.soft.webhooks.service", "Webhooks service"),
        ("src.soft.observability.otel", "OpenTelemetry observability"),
    ]
    
    rcp_success = 0
    for module, desc in rcp_tests:
        if test_import(module, desc):
            rcp_success += 1
    
    print(f"\nRCP modules: {rcp_success}/{len(rcp_tests)} OK\n")
    
    if rcp_success == len(rcp_tests):
        print("🎉 All RCP features ready!")
        return True
    else:
        print("⚠️  Some RCP features have import issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
