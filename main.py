# src/main.py
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from soft.router import app

# ---- Load .env ----
load_dotenv()

# ---- ENV FLAGS ----
DEBUG_LOG_BODY = os.getenv("DEBUG_LOG_BODY", "false").lower() in ("1", "true", "yes")

# ---- Logging global ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("smartlinks")

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ restreindre en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Middleware logging ----
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()

    # Requête entrante
    logger.info(f"➡️ {request.method} {request.url}")

    if DEBUG_LOG_BODY:
        logger.debug(f"Headers: {dict(request.headers)}")

        try:
            body = await request.body()
            if body:
                logger.debug(f"Body: {body.decode('utf-8')}")
        except Exception as e:
            logger.warning(f"Impossible de lire le body: {e}")

    # Call next
    response = await call_next(request)

    # Temps de traitement
    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"⬅️ {response.status_code} ({duration:.3f}s) {request.url.path}")

    return response

# ---- Startup hook ----
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 SmartLinks Autopilot API started (DEBUG_LOG_BODY=%s)", DEBUG_LOG_BODY)

# ---- Entrypoint ----
if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("smartlinks")
    
    try:
        logger.info("🚀 Starting SmartLinks Autopilot API...")
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload in production
            log_level="info",
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
