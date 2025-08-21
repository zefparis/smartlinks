"""Test script to verify autopilot module execution."""

import sys
import os

# Add the current directory to the path to ensure modules can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing autopilot module import...")

try:
    from src.soft.autopilot.runner import AlgorithmRunner
    from src.soft.dg.dependencies import get_db_session_factory
    print("Imports successful!")
    
    # Initialize with database session factory
    runner = AlgorithmRunner(get_db_session_factory())
    print("Autopilot runner initialized successfully.")
    print("Algorithm runner is ready to load algorithms.")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
