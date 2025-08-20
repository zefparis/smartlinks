"""
FastAPI router pour l'IASupervisor.

Inclut tous les endpoints de pilotage IA, analyse, fix et logs.
À brancher dynamiquement sur un APIRouter principal via register_ia_supervisor_routes(router).
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime

from ....models.decision import DecisionContext  # ← à adapter si le chemin change
from ...ai import IASupervisor, OperationMode
from ...dependencies import get_ia_supervisor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ia", tags=["ia_supervisor"])

# ==== MODELS ====

class AskRequest(BaseModel):
    question: str = Field(..., description="The question or instruction for the AI Supervisor")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the question")

class AskResponse(BaseModel):
    question: str
    response: str
    timestamp: str

class AnalyzeResponse(BaseModel):
    timestamp: str
    algorithms_executed: List[str]
    results: Dict[str, Any]
    ai_analysis: Dict[str, Any]
    recommended_actions: List[Dict[str, Any]]

class FixIssuesResponse(BaseModel):
    timestamp: str
    actions_executed: int
    results: List[Dict[str, Any]]

class SetModeRequest(BaseModel):
    mode: str = Field(..., description="Operation mode (auto, manual, or sandbox)")

class StatusResponse(BaseModel):
    mode: str
    last_analysis_time: Optional[str] = None
    last_action_time: Optional[str] = None
    active_actions: int
    available_algorithms: List[str]
    metrics: Dict[str, Any]

# ==== ENDPOINTS ====

@router.post("/ask", response_model=AskResponse, summary="Ask a question to the AI Supervisor")
async def ask_question(
    request: AskRequest,
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> AskResponse:
    """Ask a question or instruction to the AI Supervisor."""
    try:
        response = await supervisor.ask(request.question, request.context)
        # supervisor.ask now returns a string, not a dict
        return AskResponse(
            question=request.question,
            response=response,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Error in ask_question: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )

@router.get("/analyze", response_model=AnalyzeResponse, summary="Analyze system state")
async def analyze_system(
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> AnalyzeResponse:
    """Perform a comprehensive analysis of the system state."""
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
    """Automatically fix detected issues based on the current system state."""
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
    Modes: auto, manual, sandbox.
    """
    try:
        supervisor.set_mode(request.mode)
        return await get_status(supervisor)
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
    """Get the current status of the AI Supervisor."""
    try:
        status_data = supervisor.get_status()
        
        # Filter available_algorithms to remove None values
        available_algorithms = status_data.get("available_algorithms", [])
        filtered_algorithms = [alg for alg in available_algorithms if alg is not None and str(alg).strip()]
        
        # Ensure metrics is not None
        metrics = status_data.get("metrics", {})
        if metrics is None:
            metrics = {}
        
        # Create sanitized status data
        sanitized_status = {
            **status_data,
            "available_algorithms": filtered_algorithms,
            "metrics": metrics
        }
        
        return StatusResponse(**sanitized_status)
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
    """List all available algorithms."""
    try:
        return supervisor.get_status()["available_algorithms"]
    except Exception as e:
        logger.error(f"Error in list_algorithms: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing algorithms: {str(e)}"
        )

@router.get("/logs", response_model=List[Dict[str, Any]], summary="Get interaction logs")
async def get_logs(
    limit: int = 100,
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> List[Dict[str, Any]]:
    """Get interaction logs from the AI Supervisor."""
    try:
        status_data = supervisor.get_status()
        logs = status_data.get("metrics", {}).get("interaction_log", [])
        return logs[-limit:]
    except Exception as e:
        logger.error(f"Error in get_logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting logs: {str(e)}"
        )

@router.get("/alerts", response_model=List[Dict[str, Any]], summary="Get system alerts")
async def get_alerts(
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> List[Dict[str, Any]]:
    """Get system alerts and notifications."""
    try:
        status_data = supervisor.get_status()
        # Return alerts from metrics or empty list
        alerts = status_data.get("metrics", {}).get("alerts", [])
        return alerts
    except Exception as e:
        logger.error(f"Error in get_alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting alerts: {str(e)}"
        )

@router.get("/health", summary="IA health")
async def ia_health(supervisor: IASupervisor = Depends(get_ia_supervisor)):
    """IA health check endpoint for diagnostics."""
    try:
        _ = supervisor.get_status()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# ==== ROUTER REGISTRATION ====
def register_ia_supervisor_routes(parent_router: APIRouter):
    """
    Enregistre tous les endpoints de l’IASupervisor sur un APIRouter parent.
    Usage :
        from .routers.ia_supervisor import register_ia_supervisor_routes
        register_ia_supervisor_routes(router)
    """
    parent_router.include_router(router)
