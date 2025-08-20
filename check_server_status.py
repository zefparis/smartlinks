#!/usr/bin/env python3
"""
Check server status and diagnose issues
"""
import requests
import subprocess
import sys
import os

def check_port_8000():
    """Check if port 8000 is in use"""
    try:
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, shell=True)
        if ':8000' in result.stdout:
            print("✅ Port 8000 is in use")
            return True
        else:
            print("❌ Port 8000 is not in use")
            return False
    except Exception as e:
        print(f"Error checking port: {e}")
        return False

def check_python_processes():
    """Check for running Python processes"""
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], capture_output=True, text=True, shell=True)
        if 'python.exe' in result.stdout:
            print("✅ Python processes found")
            print(result.stdout)
            return True
        else:
            print("❌ No Python processes found")
            return False
    except Exception as e:
        print(f"Error checking processes: {e}")
        return False

def test_server_endpoints():
    """Test various server endpoints"""
    endpoints = [
        '/api/health',
        '/api/ia/health',
        '/api/ia/status',
        '/health'
    ]
    
    for endpoint in endpoints:
        try:
            url = f'http://localhost:8000{endpoint}'
            response = requests.get(url, timeout=5)
            print(f"✅ {endpoint}: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint}: Connection refused")
        except requests.exceptions.Timeout:
            print(f"⏰ {endpoint}: Timeout")
        except Exception as e:
            print(f"❌ {endpoint}: {str(e)}")

def main():
    print("=== Server Status Check ===\n")
    
    print("1. Checking port 8000...")
    port_ok = check_port_8000()
    
    print("\n2. Checking Python processes...")
    python_ok = check_python_processes()
    
    print("\n3. Testing server endpoints...")
    test_server_endpoints()
    
    print("\n=== Recommendations ===")
    if not port_ok:
        print("🔧 Server is not running. Start it with:")
        print("   python -m uvicorn src.soft.router:app --host 127.0.0.1 --port 8000 --reload")
    elif not python_ok:
        print("🔧 No Python processes found. Server might have crashed.")
        print("   Check the terminal where you started the server for error messages.")
    else:
        print("🔧 Server appears to be running but may have issues.")
        print("   Check the server logs for error messages.")

if __name__ == "__main__":
    main()
