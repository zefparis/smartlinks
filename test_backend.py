#!/usr/bin/env python3
"""Simple backend test and startup script."""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_imports():
    """Test if we can import the main components."""
    try:
        print("Testing imports...")
        from soft.router import app
        print("✅ Successfully imported FastAPI app")
        
        import uvicorn
        print("✅ uvicorn available")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def start_server():
    """Start the backend server."""
    if not test_imports():
        return False
    
    try:
        from soft.router import app
        import uvicorn
        
        print("\n🚀 Starting SmartLinks Backend Server...")
        print("📍 URL: http://127.0.0.1:8000")
        print("📚 Docs: http://127.0.0.1:8000/docs")
        print("🔍 Health: http://127.0.0.1:8000/health")
        print("\nPress Ctrl+C to stop the server\n")
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    start_server()
