from fastapi import FastAPI
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/test")
def test():
    logger.info("Test endpoint called")
    return {"status": "ok"}

if __name__ == "__main__":
    logger.info("Starting FastAPI server...")
    uvicorn.run(
        "simple_test:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    )
