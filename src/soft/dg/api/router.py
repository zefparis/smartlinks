from fastapi import APIRouter

# Main API router for DG services.
router = APIRouter()

# Plug IASupervisor routes v2 (nouvelle version robuste)
from .endpoints.ia_supervisor import router as ia_router
from ...autopilot.api import router as autopilot_router
from ...rcp.api import router as rcp_router

# Include sub-routers
router.include_router(ia_router, prefix="/api/ia", tags=["IA Supervisor"])
router.include_router(autopilot_router, prefix="/api/autopilot", tags=["Autopilot"])
router.include_router(rcp_router, prefix="/api", tags=["Runtime Control Policies"])
