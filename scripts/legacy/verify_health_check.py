import sys
import os
import subprocess
import time
import http.client
import json

def start_server():
    """Start the FastAPI server in a subprocess."""
    cmd = [sys.executable, "test_app.py"]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Give the server some time to start
    time.sleep(3)
    return process

def test_health_endpoint():
    """Test the health check endpoint."""
    conn = http.client.HTTPConnection("localhost", 8000, timeout=5)
    try:
        print("Testing health check endpoint...")
        conn.request("GET", "/api/health")
        response = conn.getresponse()
        data = json.loads(response.read().decode())
        
        print(f"Status: {response.status} {response.reason}")
        print("Response:", json.dumps(data, indent=2))
        
        if response.status != 200:
            print(f"❌ Health check failed with status {response.status}")
            return False
            
        if data.get("status") != "ok":
            print(f"❌ Unexpected status in response: {data.get('status')}")
            return False
            
        print("✅ Health check passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        return False
    finally:
        conn.close()

def main():
    print("Starting FastAPI server...")
    server_process = start_server()
    
    try:
        if not test_health_endpoint():
            print("\nServer output:")
            print(server_process.stderr.read() if server_process.stderr else "No error output")
            return 1
        return 0
    finally:
        print("\nShutting down server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    sys.exit(main())
