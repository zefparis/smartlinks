import os
import sys
import logging
from pathlib import Path

# Add src to PYTHONPATH
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("smartlinks")

def main():
    try:
        logger.info("Starting SmartLinks Autopilot...")
        
        # Import app after setting up logging
        from src.soft.router import app
        
        import uvicorn
        logger.info("Starting uvicorn server...")
        uvicorn.run(
            "src.soft.router:app",
            host="0.0.0.0",
            port=8000,
            log_level="debug"
        )
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Python path: %s", sys.path)
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
