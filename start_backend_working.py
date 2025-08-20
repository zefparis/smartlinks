#!/usr/bin/env python3
"""
Working backend startup script
"""
import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def main():
    logger.info("Starting SmartLinks backend...")
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check OpenAI key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.error("OPENAI_API_KEY not found")
        return False
    
    logger.info(f"OpenAI key found ({len(openai_key)} chars)")
    logger.info(f"Model: {os.getenv('OPENAI_MODEL', 'gpt-4o')}")
    
    # Import and start
    try:
        from soft.router import app
        logger.info("App imported successfully")
        
        import uvicorn
        logger.info("Starting uvicorn on 127.0.0.1:8000...")
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()
