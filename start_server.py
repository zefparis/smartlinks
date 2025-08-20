import uvicorn
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Starting SmartLinks Autopilot API...")
        
        # Add the project root to Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        src_path = os.path.join(project_root, 'src')
        
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        # Import the app after setting up the path
        from soft.router import app
        
        # Read runtime settings
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8000"))
        reload = os.getenv("DEBUG", "false").lower() == "true"

        logger.info(f"Starting uvicorn server on {host}:{port} (reload={reload})...")
        uvicorn.run(
            "soft.router:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
