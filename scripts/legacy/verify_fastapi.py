import sys
import logging
from fastapi import FastAPI
import uvicorn

# Configure logging to both console and file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fastapi_verify.log')
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/test")
async def test():
    logger.info("Test endpoint called")
    return {"status": "ok"}

if __name__ == "__main__":
    logger.info("=== Starting FastAPI Verification ===")
    logger.info(f"Python: {sys.version}")
    logger.info(f"FastAPI: {__import__('fastapi').__version__}")
    logger.info(f"Uvicorn: {__import__('uvicorn').__version__}")
    
    try:
        logger.info("Starting Uvicorn server...")
        uvicorn.run(
            "verify_fastapi:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=True
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
