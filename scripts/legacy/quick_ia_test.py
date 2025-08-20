import os
import sys
sys.path.append('.')

# Load environment
from dotenv import load_dotenv
load_dotenv()

print("=== IA SERVICE DIAGNOSTIC ===")

# Check environment
openai_key = os.getenv("OPENAI_API_KEY")
print(f"OPENAI_API_KEY: {'Found' if openai_key else 'Missing'}")
print(f"OPENAI_MODEL: {os.getenv('OPENAI_MODEL', 'Not set')}")

# Test imports
try:
    from src.soft.dg.ai.supervisor import IASupervisor, OperationMode
    print("✓ IASupervisor import: OK")
except Exception as e:
    print(f"✗ IASupervisor import: {e}")
    sys.exit(1)

# Test initialization
try:
    supervisor = IASupervisor(
        openai_api_key=openai_key,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        algorithm_paths=None,
        initial_mode=OperationMode.AUTO
    )
    print("✓ IASupervisor init: OK")
except Exception as e:
    print(f"✗ IASupervisor init: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test get_status
try:
    status = supervisor.get_status()
    print("✓ get_status(): OK")
    print(f"  Mode: {status.get('mode')}")
    print(f"  Available algorithms: {len(status.get('available_algorithms', []))}")
except Exception as e:
    print(f"✗ get_status(): {e}")
    import traceback
    traceback.print_exc()

print("=== DIAGNOSTIC COMPLETE ===")
