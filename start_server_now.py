#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Load environment
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    try:
        print("Starting SmartLinks backend server...")
        from soft.router import app
        import uvicorn
        
        print("Server starting on http://127.0.0.1:8000")
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
