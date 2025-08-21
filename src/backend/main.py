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

# Import scraper router with error handling
try:
    from ..soft.scraper.api import router as scraper_router
    print("✅ Scraper router imported successfully")
except Exception as e:
    print(f"❌ FAILED to import scraper router: {e}")
    try:
        # Fallback: try absolute import
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from soft.scraper.api import router as scraper_router
        print("✅ Scraper router imported with fallback method")
    except Exception as e2:
        print(f"❌ Fallback import also failed: {e2}")
        scraper_router = None

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
        
        # SELF-TEST: Test scraper endpoints
        await test_scraper_endpoints()
        
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
# Register scraper router only if import succeeded
if scraper_router:
    app.include_router(scraper_router, prefix="/api", tags=["scraper"])
    print("✅ Scraper router registered successfully")
else:
    print("❌ Scraper router NOT registered (import failed)")

# Log registered routes for diagnostics - MANDATORY
print("=" * 60)
print("REGISTERED ROUTES:")
for route in app.routes:
    methods = getattr(route, 'methods', ['UNKNOWN'])
    path = getattr(route, 'path', str(route))
    print(f"ROUTE: {path} {list(methods)}")
print("=" * 60)

async def test_scraper_endpoints():
    """Self-test all scraper endpoints at startup"""
    import httpx
    import asyncio
    
    base_url = "http://127.0.0.1:8000"  # Adjust if different
    endpoints = [
        ("GET", "/api/scraper/health"),
        ("POST", "/api/scraper/offers", {"network": "offervault", "pages": 1}),
    ]
    
    print("\n" + "=" * 60)
    print("SCRAPER SELF-TEST:")
    
    async with httpx.AsyncClient() as client:
        for method, path, *payload in endpoints:
            try:
                if method == "GET":
                    response = await client.get(f"{base_url}{path}")
                else:
                    response = await client.post(f"{base_url}{path}", json=payload[0] if payload else {})
                
                print(f"✅ {method} {path}: {response.status_code}")
                if response.status_code >= 400:
                    print(f"   ERROR: {response.text}")
                else:
                    result = response.json()
                    if path == "/api/scraper/health":
                        print(f"   Dependencies: {result.get('dependencies', {})}")
                    elif "offers" in path:
                        print(f"   Offers count: {result.get('count', 0)}")
                        
            except Exception as e:
                print(f"❌ {method} {path}: FAILED - {str(e)}")
    
    print("=" * 60 + "\n")

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
