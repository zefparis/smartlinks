import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("uvicorn")

try:
    logger.info("Starting FastAPI server...")
    uvicorn.run(
        "src.soft.router:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    )
except Exception as e:
    logger.error(f"Failed to start server: {e}", exc_info=True)
    raise
