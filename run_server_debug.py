import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("smartlinks")

def main():
    try:
        # Add src to PYTHONPATH
        src_path = str(Path(__file__).parent / "src")
        sys.path.insert(0, src_path)
        
        logger.info(f"Python path: {sys.path}")
        
        # Import app
        logger.info("Importing app...")
        from soft.router import app
        
        # Start server
        import uvicorn
        logger.info("Starting uvicorn server...")
        uvicorn.run(
            "soft.router:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="debug"
        )
    except Exception as e:
        logger.error("Fatal error:", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
