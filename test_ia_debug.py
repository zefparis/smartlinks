#!/usr/bin/env python3
"""
Debug script for IA ask endpoint 500 error
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from soft.dg.dependencies import get_ia_supervisor

async def test_ia_supervisor_directly():
    """Test IA supervisor directly without FastAPI"""
    try:
        print("=== Testing IA Supervisor Directly ===")
        
        # Get supervisor instance
        supervisor = get_ia_supervisor()
        print(f"Supervisor initialized: {supervisor is not None}")
        
        # Test status
        print("\n--- Testing get_status() ---")
        status = supervisor.get_status()
        print(f"Status: {status}")
        
        # Test ask method
        print("\n--- Testing ask() method ---")
        response = await supervisor.ask("Hello, this is a test message")
        print(f"Ask response type: {type(response)}")
        print(f"Ask response: {response}")
        
        return True
        
    except Exception as e:
        print(f"Error testing supervisor: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("=== IA Supervisor Debug Test ===\n")
    
    success = await test_ia_supervisor_directly()
    
    print(f"\nTest result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
