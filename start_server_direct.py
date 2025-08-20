#!/usr/bin/env python3
"""Direct server startup script that should work on Windows."""

import sys
import os
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Load environment
from dotenv import load_dotenv
load_dotenv()

def main():
    """Start the server directly."""
    try:
        print("🚀 Starting SmartLinks Backend Server...")
        
        # Import components
        from soft.router import app
        import uvicorn
        
        print("✅ All imports successful")
        print("📍 Server URL: http://127.0.0.1:8000")
        print("📚 API Docs: http://127.0.0.1:8000/docs")
        print("🔍 Health Check: http://127.0.0.1:8000/health")
        print("🛡️  RCP Endpoints: http://127.0.0.1:8000/api/rcp/policies")
        print("\nStarting server...")
        
        # Start server
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
