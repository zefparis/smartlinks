#!/usr/bin/env python3
"""Install missing dependencies for RCP system."""

import subprocess
import sys
import os
from pathlib import Path

def install_croniter():
    """Install croniter dependency."""
    try:
        # Get the virtual environment's pip path
        venv_pip = Path(__file__).parent / ".venv" / "Scripts" / "pip.exe"
        
        if venv_pip.exists():
            print("Installing croniter using virtual environment pip...")
            result = subprocess.run([str(venv_pip), "install", "croniter>=1.3.0"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ croniter installed successfully")
                print(result.stdout)
                return True
            else:
                print(f"❌ Failed to install croniter: {result.stderr}")
                return False
        else:
            print(f"❌ Virtual environment pip not found at {venv_pip}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing croniter: {e}")
        return False

def test_import():
    """Test if croniter can be imported."""
    try:
        import croniter
        print("✅ croniter import successful")
        return True
    except ImportError as e:
        print(f"❌ croniter import failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing RCP dependencies...")
    
    if install_croniter():
        if test_import():
            print("🎉 All dependencies are now available!")
        else:
            print("⚠️  Installation succeeded but import failed")
    else:
        print("❌ Failed to install dependencies")
