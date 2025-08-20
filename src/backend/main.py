#!/usr/bin/env python3
"""
SmartLinks Autopilot - Backend FastAPI Application
Clean architecture with proper router registration
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from .api import analytics, settings, ai, clicks, health
from .core.ai.supervisor import init_ia_supervisor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("smartlinks")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("🚀 Starting SmartLinks Autopilot API")
    try:
        # Initialize database and core services
        from .startup import initialize_application
        await initialize_application()
        
        # Initialize AI Supervisor
        init_ia_supervisor()
        logger.info("✅ AI Supervisor initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down SmartLinks Autopilot API")

# Create FastAPI application
app = FastAPI(
    title="SmartLinks Autopilot API",
    description="Analytics and AI-powered link management platform",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://*.railway.app",
        "https://*.vercel.app",
        "https://*.netlify.app",
        os.getenv("FRONTEND_URL", "")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(clicks.router, prefix="/api/clicks", tags=["clicks"])

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "SmartLinks Autopilot API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check"""
    return {"status": "healthy", "service": "smartlinks-api"}

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Server starting on {host}:{port}")
    uvicorn.run(
        "src.backend.main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
        log_level="info"
    )
