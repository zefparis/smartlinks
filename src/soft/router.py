import traceback
import logging
from typing import Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dotenv import load_dotenv
load_dotenv()

from fastapi import APIRouter
from .admin import admin_router
from .api_router import api_router as base_api_router

# Import API routers
from .api import (
    clicks_router,
    config_router,
    assistant_router,
    dg_router,
    ai_discovery_router,
    creators_router
)

# Import other routers
from .api.ai_dg_router import router as ai_dg_router
from .api.services_router import router as services_router
from .api.analytics_router import router as analytics_router
from .api.analytics_schema_router import router as analytics_schema_router
from .api.settings_router import router as settings_router
from .api.health_router import router as health_router
from .dg.api.endpoints.ia_supervisor import register_ia_supervisor_routes
from .dg.dependencies import init_ia_supervisor
from .rcp.api import router as rcp_router

# Import new feature routers (commented out temporarily to fix startup)
# from .pac.api import router as pac_router
# from .replay.api import router as replay_router
# from .features.api import router as features_router
# from .bandits.api import router as bandits_router
# from .optimizer.api import router as optimizer_router
# from .backtesting.api import router as backtesting_router
# from .webhooks.api import router as webhooks_router

# Import payment system routers
from .payments.api import router as payments_router
from .payments.finance_api import router as finance_router

# Logger global
logger = logging.getLogger("smartlinks")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="SmartLinks Autopilot API",
    version="1.0.0",
    debug=True,  # Active debug pour dev
)

# Add basic health endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "SmartLinks Autopilot API", "status": "running", "docs": "/docs"}

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Middleware global erreurs ---
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.exception("Unhandled exception occurred")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": str(e) if app.debug else "See logs",
                "debug": traceback.format_exc() if app.debug else None,
            },
        )

# --- Routes ---
# Include all API routers with appropriate prefixes

# Core API routes under /api
app.include_router(base_api_router, prefix="/api")
app.include_router(clicks_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(analytics_schema_router, prefix="/api")
app.include_router(ai_discovery_router, prefix="/api")
app.include_router(assistant_router, prefix="/api")
app.include_router(dg_router, prefix="/api")
app.include_router(ai_dg_router, prefix="/api")
app.include_router(services_router, prefix="/api")

# Include new feature routers (commented out - not yet implemented)
# app.include_router(pac_router, prefix="/api")
# app.include_router(replay_router, prefix="/api")
# app.include_router(features_router, prefix="/api")
# app.include_router(bandits_router, prefix="/api")
# app.include_router(optimizer_router, prefix="/api")
# app.include_router(backtesting_router, prefix="/api")
# app.include_router(webhooks_router, prefix="/api")

# Include payment system routers
app.include_router(payments_router, prefix="/api")
app.include_router(finance_router, prefix="/api")

# IA Supervisor routes (under /api/ia)
register_ia_supervisor_routes(app)

# Admin routes under /admin
app.include_router(admin_router, prefix="/admin")

# --- Startup: initialize IASupervisor ---
@app.on_event("startup")
async def init_ia_on_startup():
    """Initialize the IASupervisor singleton."""
    try:
        init_ia_supervisor()
        logger.info("IASupervisor initialized on startup")
    except Exception as e:
        logger.error(f"Failed to initialize IASupervisor: {e}", exc_info=True)

# --- Startup logs ---
@app.on_event("startup")
async def print_routes():
    """Print all available routes on startup in a clean format."""
    import inspect
    from fastapi.routing import APIRoute
    
    # Collect all routes
    routes = []
    for route in app.routes:
        if not (hasattr(route, "methods") and hasattr(route, "path")):
            continue
            
        # Skip HEAD/OPTIONS and internal routes
        methods = [m for m in route.methods if m not in {"HEAD", "OPTIONS"}]
        if not methods:
            continue
            
        # Get endpoint summary from docstring
        summary = ""
        if hasattr(route, "endpoint"):
            if inspect.isfunction(route.endpoint) or inspect.ismethod(route.endpoint):
                summary = (route.endpoint.__doc__ or "").split("\n")[0].strip()
        
        routes.append({
            "path": route.path,
            "method": methods[0],  # Just show one method per line for cleaner output
            "summary": summary
        })
    
    # Sort routes by path
    routes.sort(key=lambda x: x["path"])
    
    # Print the routes in a clean format
    logger.info("\n=== Available Routes ===")
    for route in routes:
        method = route["method"]
        path = route["path"]
        summary = f"  # {route['summary']}" if route["summary"] else ""
        logger.info(f"{method:6} {path}{summary}")
    
    # Print additional info
    logger.info("\nAPI Documentation: http://localhost:8000/docs")
    logger.info("Health Check:     http://localhost:8000/api/health")
    logger.info("=" * 50 + "\n")

@app.get("/api/routes", include_in_schema=False)
async def list_routes():
    """
    List all available API routes with their methods and summaries.
    Useful for debugging and API exploration.
    """
    routes = []
    for route in app.routes:
        if not (hasattr(route, "methods") and hasattr(route, "path")):
            continue
            
        methods = sorted(list(route.methods - {"HEAD", "OPTIONS"}))
        if not methods:
            continue
            
        # Get endpoint summary from docstring
        summary = ""
        if hasattr(route, "endpoint") and route.endpoint.__doc__:
            summary = route.endpoint.__doc__.split("\n")[0].strip()
            
        routes.append({
            "path": route.path,
            "methods": methods,
            "summary": summary,
            "name": route.name
        })
    
    # Sort routes by path
    routes.sort(key=lambda x: x["path"])
    return {"routes": routes}

# --- Script direct ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.soft.router:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
