#!/usr/bin/env python3
"""
Simple server startup that ensures IA service comes online
"""
import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def main():
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    logger.info("Starting SmartLinks backend with IA service...")
    
    # Verify OpenAI key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.error("OPENAI_API_KEY not found in environment")
        return False
    
    logger.info(f"OpenAI API key found ({len(openai_key)} chars)")
    
    # Test IA Supervisor before starting server
    try:
        from soft.dg.ai.supervisor import IASupervisor, OperationMode
        from soft.dg.dependencies import init_ia_supervisor
        
        logger.info("Testing IA Supervisor initialization...")
        init_ia_supervisor()
        logger.info("IA Supervisor initialized successfully")
        
    except Exception as e:
        logger.error(f"IA Supervisor initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Start server
    logger.info("Starting uvicorn server...")
    import uvicorn
    uvicorn.run(
        "soft.router:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("Failed to start server")
        sys.exit(1)
