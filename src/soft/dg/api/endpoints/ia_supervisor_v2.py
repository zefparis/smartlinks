"""
Endpoints FastAPI pour l'IA Supervisor - Version 2.0

Endpoints robustes avec gestion d'erreurs complète, mode dégradé,
et intégration avec la nouvelle architecture OpenAI Factory.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel, Field
from datetime import datetime

from ...ai.supervisor import IASupervisor, OperationMode
from ...dependencies import get_ia_supervisor

logger = logging.getLogger(__name__)

# Router principal pour les endpoints IA
router = APIRouter(
    prefix="/api/ia",
    tags=["ia_supervisor"],
    responses={
        404: {"description": "Endpoint non trouvé"},
        500: {"description": "Erreur interne du serveur"},
        503: {"description": "Service temporairement indisponible"}
    }
)

# ====== MODELS PYDANTIC ======

class AskRequest(BaseModel):
    """Requête pour poser une question à l'IA Supervisor."""
    question: str = Field(..., description="Question ou instruction pour l'IA Supervisor", min_length=1)
    context: Optional[Dict[str, Any]] = Field(None, description="Contexte additionnel pour la question")

class AskResponse(BaseModel):
    """Réponse à une question de l'IA Supervisor."""
    question: str
    response: str
    timestamp: str
    degraded_mode: bool = Field(default=False, description="True si réponse en mode dégradé")

class AnalyzeResponse(BaseModel):
    """Réponse d'analyse système."""
    timestamp: str
    algorithms_executed: List[str]
    results: Dict[str, Any]
    ai_analysis: Dict[str, Any]
    recommended_actions: List[Dict[str, Any]]
    degraded_mode: bool = Field(default=False, description="True si analyse en mode dégradé")

class FixIssuesResponse(BaseModel):
    """Réponse de correction d'issues."""
    timestamp: str
    actions_executed: int
    results: List[Dict[str, Any]]
    mode: str = Field(description="Mode d'exécution (auto/sandbox)")

class SetModeRequest(BaseModel):
    """Requête pour changer le mode d'opération."""
    mode: str = Field(..., description="Mode d'opération: auto, manual, ou sandbox")

class StatusResponse(BaseModel):
    """Réponse de statut du supervisor."""
    mode: str
    degraded_mode: bool
    last_analysis_time: Optional[str] = None
    last_action_time: Optional[str] = None
    active_actions: int
    available_algorithms: List[str]
    openai_status: str
    is_ready: bool
    metrics: Dict[str, Any]

class SelfcheckResponse(BaseModel):
    """Réponse du diagnostic complet."""
    timestamp: str
    global_status: str = Field(description="ready, degraded, ou unavailable")
    supervisor_status: Dict[str, Any]
    openai_status: Dict[str, Any]
    tests: Dict[str, Any]

class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée."""
    error: str
    detail: str
    timestamp: str
    status_code: int

# ====== HELPERS ======

def create_error_response(
    status_code: int,
    error: str,
    detail: str
) -> HTTPException:
    """Crée une réponse d'erreur standardisée."""
    error_data = ErrorResponse(
        error=error,
        detail=detail,
        timestamp=datetime.utcnow().isoformat(),
        status_code=status_code
    )
    return HTTPException(status_code=status_code, detail=error_data.dict())

async def safe_supervisor_call(supervisor_func, error_message: str):
    """Wrapper pour appels sécurisés au supervisor avec gestion d'erreurs."""
    try:
        return await supervisor_func()
    except Exception as e:
        logger.error(f"{error_message}: {e}", exc_info=True)
        raise create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Erreur IA Supervisor",
            detail=f"{error_message}: {str(e)}"
        )

# ====== ENDPOINTS ======

@router.post("/ask", response_model=AskResponse, summary="Poser une question à l'IA Supervisor")
async def ask_question(
    request: AskRequest,
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> AskResponse:
    """
    Pose une question ou donne une instruction à l'IA Supervisor.
    
    Gère automatiquement le mode dégradé si OpenAI est indisponible.
    """
    logger.info(f"Question reçue: {request.question[:100]}...")
    
    try:
        response_data = await supervisor.ask(request.question, request.context)
        
        # Détection du mode dégradé basé sur la réponse
        degraded = "indisponible" in response_data.get("response", "").lower()
        
        return AskResponse(
            question=response_data["question"],
            response=response_data["response"],
            timestamp=response_data["timestamp"],
            degraded_mode=degraded
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la question: {e}", exc_info=True)
        raise create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Erreur traitement question",
            detail=f"Impossible de traiter la question: {str(e)}"
        )

@router.get("/analyze", response_model=AnalyzeResponse, summary="Analyser l'état du système")
async def analyze_system(
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> AnalyzeResponse:
    """
    Effectue une analyse complète de l'état du système.
    
    Exécute tous les algorithmes disponibles et fournit une analyse IA.
    """
    logger.info("Démarrage analyse système")
    
    async def analysis_func():
        return await supervisor.analyze_system()
    
    result = await safe_supervisor_call(
        analysis_func,
        "Erreur lors de l'analyse système"
    )
    
    # Détection du mode dégradé
    ai_analysis = result.get("ai_analysis", {})
    degraded = ai_analysis.get("summary") == "Analyse IA indisponible"
    
    return AnalyzeResponse(
        timestamp=result["timestamp"],
        algorithms_executed=result["algorithms_executed"],
        results=result["results"],
        ai_analysis=result["ai_analysis"],
        recommended_actions=result["recommended_actions"],
        degraded_mode=degraded
    )

@router.post("/fix", response_model=FixIssuesResponse, summary="Corriger les issues détectées")
async def fix_issues(
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> FixIssuesResponse:
    """
    Corrige automatiquement les issues détectées selon le mode d'opération.
    
    - Mode AUTO: Exécute les actions automatiquement
    - Mode SANDBOX: Simule les actions sans les exécuter
    - Mode MANUAL: Retourne une erreur
    """
    logger.info("Démarrage correction des issues")
    
    # Vérification du mode
    status_data = supervisor.get_status()
    current_mode = status_data.get("mode", "auto")
    
    if current_mode == "manual":
        raise create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="Mode manuel actif",
            detail="Impossible de corriger automatiquement en mode manuel. Changez vers auto ou sandbox."
        )
    
    async def fix_func():
        return await supervisor.fix_detected_issues()
    
    result = await safe_supervisor_call(
        fix_func,
        "Erreur lors de la correction des issues"
    )
    
    return FixIssuesResponse(
        timestamp=result["timestamp"],
        actions_executed=result["actions_executed"],
        results=result["results"],
        mode=current_mode
    )

@router.post("/switch-mode", response_model=StatusResponse, summary="Changer le mode d'opération")
async def switch_mode(
    request: SetModeRequest,
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> StatusResponse:
    """
    Change le mode d'opération de l'IA Supervisor.
    
    Modes disponibles:
    - auto: Mode autonome (exécute les actions automatiquement)
    - manual: Mode manuel (requiert approbation humaine)
    - sandbox: Mode simulation (simule sans exécuter)
    """
    logger.info(f"Changement de mode vers: {request.mode}")
    
    # Validation du mode
    valid_modes = ["auto", "manual", "sandbox"]
    if request.mode.lower() not in valid_modes:
        raise create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="Mode invalide",
            detail=f"Mode '{request.mode}' invalide. Modes valides: {', '.join(valid_modes)}"
        )
    
    try:
        supervisor.set_mode(request.mode.lower())
        return await get_status(supervisor)
        
    except Exception as e:
        logger.error(f"Erreur changement de mode: {e}", exc_info=True)
        raise create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Erreur changement mode",
            detail=f"Impossible de changer le mode: {str(e)}"
        )

@router.get("/status", response_model=StatusResponse, summary="Obtenir le statut actuel")
async def get_status(
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> StatusResponse:
    """
    Retourne le statut actuel de l'IA Supervisor.
    
    Inclut le mode d'opération, les métriques, et l'état OpenAI.
    """
    try:
        status_data = supervisor.get_status()
        openai_status = supervisor.openai_factory.get_status()
        
        return StatusResponse(
            mode=status_data["mode"],
            degraded_mode=getattr(supervisor, '_degraded_mode', False),
            last_analysis_time=status_data.get("last_analysis_time"),
            last_action_time=status_data.get("last_action_time"),
            active_actions=status_data["active_actions"],
            available_algorithms=status_data["available_algorithms"],
            openai_status=openai_status["status"],
            is_ready=supervisor.is_ready(),
            metrics=status_data["metrics"]
        )
        
    except Exception as e:
        logger.error(f"Erreur récupération statut: {e}", exc_info=True)
        raise create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Erreur récupération statut",
            detail=f"Impossible de récupérer le statut: {str(e)}"
        )

@router.get("/selfcheck", response_model=SelfcheckResponse, summary="Diagnostic complet du système")
async def selfcheck(
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> SelfcheckResponse:
    """
    Effectue un diagnostic complet de l'IA Supervisor.
    
    Teste la connectivité OpenAI, les algorithmes, et les fonctionnalités principales.
    Retourne un rapport détaillé avec le statut global.
    """
    logger.info("Démarrage selfcheck complet")
    
    async def selfcheck_func():
        return await supervisor.selfcheck()
    
    result = await safe_supervisor_call(
        selfcheck_func,
        "Erreur lors du selfcheck"
    )
    
    return SelfcheckResponse(
        timestamp=result["timestamp"],
        global_status=result["global_status"],
        supervisor_status=result["supervisor_status"],
        openai_status=result["openai_status"],
        tests=result["tests"]
    )

@router.get("/algorithms", response_model=List[str], summary="Lister les algorithmes disponibles")
async def list_algorithms(
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> List[str]:
    """
    Retourne la liste de tous les algorithmes disponibles.
    """
    try:
        status_data = supervisor.get_status()
        return status_data["available_algorithms"]
        
    except Exception as e:
        logger.error(f"Erreur listage algorithmes: {e}", exc_info=True)
        raise create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Erreur listage algorithmes",
            detail=f"Impossible de lister les algorithmes: {str(e)}"
        )

@router.get("/logs", response_model=List[Dict[str, Any]], summary="Récupérer les logs d'interaction")
async def get_logs(
    limit: int = Query(default=100, ge=1, le=1000, description="Nombre maximum de logs à retourner"),
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> List[Dict[str, Any]]:
    """
    Retourne les logs d'interaction avec l'IA Supervisor.
    
    Limité aux dernières interactions pour éviter la surcharge.
    """
    try:
        status_data = supervisor.get_status()
        logs = status_data.get("metrics", {}).get("interaction_log", [])
        
        # Retourner les derniers logs selon la limite
        return logs[-limit:] if logs else []
        
    except Exception as e:
        logger.error(f"Erreur récupération logs: {e}", exc_info=True)
        raise create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Erreur récupération logs",
            detail=f"Impossible de récupérer les logs: {str(e)}"
        )

@router.get("/health", summary="Vérification de santé simple")
async def health_check(
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> Dict[str, Any]:
    """
    Endpoint de vérification de santé simple pour les load balancers.
    
    Retourne un statut rapide sans exécuter de tests lourds.
    """
    try:
        is_ready = supervisor.is_ready()
        openai_status = supervisor.openai_factory.get_status()
        
        return {
            "status": "healthy" if is_ready else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "openai_available": openai_status["status"] in ["ready", "degraded"],
            "algorithms_count": len(supervisor.registry.get_available_algorithms())
        }
        
    except Exception as e:
        logger.error(f"Erreur health check: {e}", exc_info=True)
        raise create_error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error="Service indisponible",
            detail="Le service IA Supervisor est temporairement indisponible"
        )

# ====== REGISTRATION HELPER ======

def register_ia_supervisor_routes(parent_router: APIRouter) -> None:
    """
    Enregistre tous les endpoints de l'IA Supervisor sur un router parent.
    
    Usage:
        from .endpoints.ia_supervisor_v2 import register_ia_supervisor_routes
        register_ia_supervisor_routes(app_router)
    """
    parent_router.include_router(router)
    logger.info("Endpoints IA Supervisor v2 enregistrés sur /api/ia")
