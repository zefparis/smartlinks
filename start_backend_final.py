#!/usr/bin/env python3
import sys
import os
import subprocess
import time

def kill_port_8000():
    try:
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if ':8000' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        subprocess.run(['taskkill', '/F', '/PID', pid], shell=True)
                        print(f'Killed process {pid} on port 8000')
    except:
        pass

def start_backend():
    print('🔧 Cleaning port 8000...')
    kill_port_8000()
    time.sleep(2)
    
    # Set up paths
    sys.path.insert(0, '.')
    sys.path.insert(0, 'src')
    
    print('🚀 Starting SmartLinks Backend Server')
    print('Host: http://localhost:8000')
    print('Analytics: http://localhost:3000/analytics')
    print('-' * 40)
    
    try:
        from main import app
        import uvicorn
        
        print('✅ App loaded successfully')
        print('🌐 Server starting...')
        
        uvicorn.run(
            app, 
            host='0.0.0.0', 
            port=8000, 
            log_level='info',
            access_log=True
        )
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        input('Press Enter to exit...')

if __name__ == '__main__':
    start_backend()
