#!/usr/bin/env python3
"""
Start backend server with proper error handling and logging
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Start the backend server"""
    try:
        # Change to project directory
        project_dir = Path(__file__).parent
        os.chdir(project_dir)
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Load environment variables
        env_file = project_dir / '.env'
        if env_file.exists():
            logger.info("Loading .env file...")
            from dotenv import load_dotenv
            load_dotenv(env_file)
        else:
            logger.warning("No .env file found")
        
        # Start uvicorn server
        cmd = [
            sys.executable, "-m", "uvicorn",
            "src.soft.router:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload"
        ]
        
        logger.info(f"Starting server with command: {' '.join(cmd)}")
        
        # Run the server
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line.rstrip())
            
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
