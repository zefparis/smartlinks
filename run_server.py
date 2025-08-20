import sys
import os
import logging
from fastapi import FastAPI
import uvicorn

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("smartlinks")

# Import the FastAPI app from the router module
try:
    from src.soft.router import app
    logger.info("Successfully imported FastAPI app from src.soft.router")
except Exception as e:
    logger.error(f"Failed to import FastAPI app: {e}")
    raise

if __name__ == "__main__":
    try:
        logger.info("Starting Uvicorn server...")
        uvicorn.run(
            "run_server:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise
