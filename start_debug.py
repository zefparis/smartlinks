import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("smartlinks")

# Add src to PYTHONPATH
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

try:
    logger.info("Trying to import app...")
    from soft.router import app
    logger.info("Successfully imported app")
    
    if __name__ == "__main__":
        import uvicorn
        logger.info("Starting uvicorn server...")
        uvicorn.run(
            "soft.router:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="debug"
        )
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Python path: %s", sys.path)
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise
