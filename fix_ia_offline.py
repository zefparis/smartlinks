#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment
from dotenv import load_dotenv
load_dotenv()

print("=== FIXING IA OFFLINE ISSUE ===")

# Check environment
openai_key = os.getenv("OPENAI_API_KEY")
print(f"OPENAI_API_KEY: {'Found' if openai_key else 'MISSING'}")

if not openai_key:
    print("ERROR: No OpenAI API key found")
    sys.exit(1)

# Test IA Supervisor
try:
    from soft.dg.ai.supervisor import IASupervisor, OperationMode
    
    supervisor = IASupervisor(
        openai_api_key=openai_key,
        openai_model="gpt-4o",
        algorithm_paths=None,
        initial_mode=OperationMode.AUTO
    )
    
    status = supervisor.get_status()
    print(f"IA Status: {status}")
    print("SUCCESS: IA Supervisor working")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Start server with IA
print("\nStarting server with IA...")
import uvicorn
uvicorn.run(
    "soft.router:app",
    host="127.0.0.1", 
    port=8000,
    reload=False,
    log_level="info"
)
