#!/usr/bin/env python3
"""
Simple IA service test to identify why it's offline
"""
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_ia_service():
    print("=== IA SERVICE DIAGNOSTIC ===")
    
    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Environment loaded")
    except Exception as e:
        print(f"✗ Environment load failed: {e}")
        return False
    
    # Check OpenAI key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("✗ OPENAI_API_KEY missing")
        return False
    print(f"✓ OPENAI_API_KEY found ({len(openai_key)} chars)")
    
    # Test imports
    try:
        from soft.dg.ai.supervisor import IASupervisor, OperationMode
        print("✓ IASupervisor imported")
    except Exception as e:
        print(f"✗ IASupervisor import failed: {e}")
        return False
    
    # Test initialization
    try:
        supervisor = IASupervisor(
            openai_api_key=openai_key,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            algorithm_paths=None,
            initial_mode=OperationMode.AUTO
        )
        print("✓ IASupervisor initialized")
    except Exception as e:
        print(f"✗ IASupervisor init failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test get_status
    try:
        status = supervisor.get_status()
        print("✓ get_status() works")
        print(f"  Mode: {status.get('mode')}")
        print(f"  OpenAI: {status.get('openai_status')}")
    except Exception as e:
        print(f"✗ get_status() failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n=== IA SERVICE READY ===")
    return True

if __name__ == "__main__":
    success = test_ia_service()
    if not success:
        print("\n=== ISSUES FOUND ===")
        print("Fix the errors above before starting the server")
    sys.exit(0 if success else 1)
