import os
import logging
from dotenv import load_dotenv
import openai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("--- Starting OpenAI Client Verification ---")

try:
    logger.info("Loading .env file...")
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment.")
        raise ValueError("Missing OPENAI_API_KEY")
    
    logger.info("API key loaded. Attempting to initialize AsyncOpenAI client...")
    
    client = openai.AsyncOpenAI(api_key=api_key)
    
    logger.info("✅ OpenAI client initialized successfully!")
    
except Exception as e:
    logger.error(f"❌ An error occurred: {e}", exc_info=True)

logger.info("--- OpenAI Client Verification Finished ---")
