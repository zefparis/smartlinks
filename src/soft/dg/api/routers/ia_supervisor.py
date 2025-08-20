"""
FastAPI router for the AI Supervisor API endpoints.
"""
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime

from ....models.decision import DecisionContext
from ....config import ai_supervisor_config
from ...dependencies import get_ia_supervisor
from ....ai import IASupervisor, OperationMode

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ia", tags=["ai_supervisor"])

# Request/Response Models
class AskRequest(BaseModel):
    """Request model for asking a question to the AI Supervisor."""
    question: str = Field(..., description="The question or instruction for the AI Supervisor")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the question")

class AskResponse(BaseModel):
    """Response model for AI Supervisor questions."""
    question: str
    response: str
    timestamp: str

class AnalyzeResponse(BaseModel):
    """Response model for system analysis."""
    timestamp: str
    algorithms_executed: List[str]
    results: Dict[str, Any]
    ai_analysis: Dict[str, Any]
    recommended_actions: List[Dict[str, Any]]

class FixIssuesResponse(BaseModel):
    """Response model for issue fixing."""
    timestamp: str
    actions_executed: int
    results: List[Dict[str, Any]]

class SetModeRequest(BaseModel):
    """Request model for changing operation mode."""
    mode: str = Field(..., description="Operation mode (auto, manual, or sandbox)")

class StatusResponse(BaseModel):
    """Response model for system status."""
    mode: str
    last_analysis_time: Optional[str] = None
    last_action_time: Optional[str] = None
    active_actions: int
    available_algorithms: List[str]
    metrics: Dict[str, Any]

class LogEntry(BaseModel):
    """Model for log entries."""
    timestamp: str
    type: str
    content: str
    response: str
    context: Dict[str, Any]

class SimulationRequest(BaseModel):
    """Request model for traffic simulation."""
    duration_hours: int = Field(24, description="Duration of the simulation in hours")
    resolution_minutes: int = Field(5, description="Time resolution in minutes")
    baseline_traffic: int = Field(1000, description="Baseline traffic volume")
    anomaly_intensity: float = Field(3.0, description="Intensity of anomalies to inject")

# Endpoints
@router.post("/ask", response_model=AskResponse, summary="Ask a question to the AI Supervisor")
async def ask_question(
    request: AskRequest,
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> AskResponse:
    """
    Ask a question or give an instruction to the AI Supervisor.
    """
    try:
        response = await supervisor.ask(request.question, request.context or {})
        return AskResponse(**response)
    except Exception as e:
        logger.error(f"Error in ask_question: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )

@router.get("/alerts", response_model=List[Dict[str, Any]], summary="Get current alerts")
async def get_alerts(
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> List[Dict[str, Any]]:
    """
    Get current alerts maintained by the AI Supervisor.
    """
    try:
        # Alerts are stored on supervisor.state.alerts as a list of dicts
        alerts = getattr(supervisor, "state", None)
        if alerts and isinstance(supervisor.state.alerts, list):
            return supervisor.state.alerts
        return []
    except Exception as e:
        logger.error(f"Error in get_alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting alerts: {str(e)}"
        )

@router.get("/analyze", response_model=AnalyzeResponse, summary="Analyze system state")
async def analyze_system(
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> AnalyzeResponse:
    """
    Perform a comprehensive analysis of the system state.
    """
    try:
        result = await supervisor.analyze_system()
        return AnalyzeResponse(**result)
    except Exception as e:
        logger.error(f"Error in analyze_system: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing system: {str(e)}"
        )

@router.post("/fix", response_model=FixIssuesResponse, summary="Fix detected issues")
async def fix_issues(
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> FixIssuesResponse:
    """
    Automatically fix detected issues based on the current system state.
    """
    try:
        result = await supervisor.fix_detected_issues()
        return FixIssuesResponse(**result)
    except Exception as e:
        logger.error(f"Error in fix_issues: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fixing issues: {str(e)}"
        )

@router.post("/switch-mode", response_model=StatusResponse, summary="Change operation mode")
async def switch_mode(
    request: SetModeRequest,
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> StatusResponse:
    """
    Change the operation mode of the AI Supervisor.
    
    Modes:
    - auto: Autonomous mode (takes actions automatically)
    - manual: Manual mode (requires human approval for actions)
    - sandbox: Sandbox mode (simulates actions without executing them)
    """
    try:
        supervisor.set_mode(request.mode)
        status_data = supervisor.get_status()
        return StatusResponse(**status_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode: {request.mode}. Must be one of: auto, manual, sandbox"
        )
    except Exception as e:
        logger.error(f"Error in switch_mode: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error changing mode: {str(e)}"
        )

@router.get("/status", response_model=StatusResponse, summary="Get current status")
async def get_status(
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> StatusResponse:
    """
    Get the current status of the AI Supervisor.
    """
    try:
        status_data = supervisor.get_status()
        return StatusResponse(**status_data)
    except Exception as e:
        logger.error(f"Error in get_status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting status: {str(e)}"
        )

@router.get("/algorithms", response_model=List[str], summary="List available algorithms")
async def list_algorithms(
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> List[str]:
    """
    Get a list of all available algorithms.
    """
    try:
        return supervisor.get_status()["available_algorithms"]
    except Exception as e:
        logger.error(f"Error in list_algorithms: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing algorithms: {str(e)}"
        )

@router.get("/logs", response_model=List[LogEntry], summary="Get interaction logs")
async def get_logs(
    limit: int = 100,
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> List[LogEntry]:
    """
    Get interaction logs from the AI Supervisor.
    """
    try:
        status_data = supervisor.get_status()
        logs = status_data.get("metrics", {}).get("interaction_log", [])
        return [LogEntry(**log) for log in logs[-limit:]]
    except Exception as e:
        logger.error(f"Error in get_logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting logs: {str(e)}"
        )

@router.post("/simulate", summary="Run a traffic simulation")
async def simulate_traffic(
    request: SimulationRequest,
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> Dict[str, Any]:
    """
    Run a traffic simulation with the specified parameters.
    """
    try:
        # In a real implementation, this would call the traffic simulation algorithm
        # For now, we'll return a simulated response
        return {
            "status": "success",
            "message": f"Simulation completed for {request.duration_hours} hours",
            "parameters": request.dict(),
            "results": {
                "total_requests": request.duration_hours * 60 // request.resolution_minutes * request.baseline_traffic,
                "anomalies_detected": 3,
                "average_latency_ms": 45.2,
                "error_rate": 0.012
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in simulate_traffic: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running simulation: {str(e)}"
        )

@router.get("/config", summary="Get current configuration")
async def get_config() -> Dict[str, Any]:
    """
    Get the current configuration of the AI Supervisor.
    """
    try:
        # Return a sanitized version of the config (without sensitive data)
        config = {
            "openai_model": ai_supervisor_config.openai_model,
            "default_mode": ai_supervisor_config.default_mode,
            "log_level": ai_supervisor_config.log_level,
            "log_file": ai_supervisor_config.log_file,
            "alert_cooldown_minutes": ai_supervisor_config.alert_cooldown_minutes,
            "max_concurrent_repairs": ai_supervisor_config.max_concurrent_repairs,
            "rate_limit_requests": ai_supervisor_config.rate_limit_requests,
            "rate_limit_period": ai_supervisor_config.rate_limit_period,
            "cache_ttl": ai_supervisor_config.cache_ttl,
            "algorithm_paths": ai_supervisor_config.algorithm_paths
        }
        return config
    except Exception as e:
        logger.error(f"Error in get_config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting configuration: {str(e)}"
        )

# Add error handler for 404
def register_handlers(app):
    """Register error handlers for the API."""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

# Register the router in the FastAPI app
def register_ia_supervisor_routes(app):
    """Register the IA Supervisor routes with the FastAPI app."""
    app.include_router(router)
    register_handlers(app)
    
    # Add CORS middleware if not already added
    from fastapi.middleware.cors import CORSMiddleware
    
    # app.user_middleware stores Middleware objects; compare the class
    if not any(getattr(m, "cls", None) is CORSMiddleware for m in app.user_middleware):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, replace with specific origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    logger.info("IA Supervisor routes registered")
