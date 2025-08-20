import uvicorn
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

logger.info("--- Verifying Uvicorn --- ")
try:
    logger.info("Attempting to run a non-existent app with uvicorn...")
    # This should fail with an ImportError, which is the expected behavior.
    uvicorn.run("non_existent_app:app", host="127.0.0.1", port=8000)
    logger.info("Uvicorn finished unexpectedly without an error.")
except ImportError as e:
    logger.info(f"✅ SUCCESS: Uvicorn correctly raised an ImportError as expected: {e}")
except Exception as e:
    logger.error(f"❌ FAILURE: Uvicorn failed with an unexpected error: {e}", exc_info=True)

logger.info("--- Uvicorn Verification Finished ---")
