#!/usr/bin/env python3
"""Install croniter dependency directly."""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Install croniter using subprocess."""
    try:
        # Get the virtual environment's pip path
        venv_root = Path(__file__).parent / ".venv"
        pip_exe = venv_root / "Scripts" / "pip.exe"
        python_exe = venv_root / "Scripts" / "python.exe"
        
        print(f"Using pip: {pip_exe}")
        print(f"Using python: {python_exe}")
        
        if not pip_exe.exists():
            print(f"❌ pip.exe not found at {pip_exe}")
            return False
            
        # Install croniter
        print("Installing croniter...")
        result = subprocess.run([
            str(pip_exe), "install", "croniter>=1.3.0"
        ], capture_output=True, text=True, shell=True)
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        if result.returncode == 0:
            print("✅ croniter installed successfully")
            
            # Test import
            test_result = subprocess.run([
                str(python_exe), "-c", "import croniter; print('croniter import successful')"
            ], capture_output=True, text=True, shell=True)
            
            print(f"Test result: {test_result.stdout}")
            if test_result.returncode == 0:
                print("✅ croniter import test passed")
                return True
            else:
                print(f"❌ croniter import test failed: {test_result.stderr}")
                return False
        else:
            print(f"❌ Failed to install croniter")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 croniter is now available! You can restart the backend server.")
    else:
        print("\n❌ Failed to install croniter. Please install manually.")
    
    input("Press Enter to continue...")
