import os
import sys
import logging
from fastapi import FastAPI, Request
import uvicorn

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("smartlinks")

# Create a simple FastAPI app for testing
app = FastAPI()

@app.get("/test")
async def test():
    return {"message": "Test endpoint is working!"}

# Try to import and mount the main app
try:
    from src.soft.router import app as main_app
    app.mount("", main_app)
    logger.info("Successfully mounted main FastAPI application")
except Exception as e:
    logger.error(f"Failed to import or mount main application: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        logger.info("Starting Uvicorn server...")
        uvicorn.run(
            "start_backend:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        raise
