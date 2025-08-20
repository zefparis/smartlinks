"""
API FastAPI pour le DG autonome avec intégration IA Supervisor.

Module principal exposant les endpoints REST pour interagir avec le DG :
- Status, décisions, actions, algorithmes, analyse (DG classique)
- Endpoints IA Supervisor (/api/ia/*) pour l'intelligence artificielle

Architecture modulaire avec séparation claire entre DG et IA.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ..core.engine import DGEngine, DGMode
from ..models.decision import Decision, Action, DecisionStatus, DecisionType
from ..monitoring.logger import DGLogger
from ..dependencies import init_ia_supervisor

# ROUTER PRINCIPAL DG
router = APIRouter(
    prefix="/api/dg",
    tags=["dg"],
    responses={404: {"description": "Not found"}},
)

# Dependency pour injection du moteur DG (pas de global state !)
def get_dg_engine(request: Request) -> DGEngine:
    dg_engine: DGEngine = request.app.state.dg_engine
    if not dg_engine:
        raise RuntimeError("DG Engine n'a pas été initialisé sur app.state")
    return dg_engine

_logger = DGLogger("api")

# ====== MODELS POUR LES REQUÊTES PATCH/POST ======
class AlgorithmConfigUpdate(BaseModel):
    config: Dict[str, Any]

# ========== STATUS ==========

@router.get("/status", response_model=Dict[str, Any])
async def get_status(engine: DGEngine = Depends(get_dg_engine)):
    """Récupère l'état actuel du DG autonome."""
    return engine.get_status()

@router.get("/mode", response_model=Dict[str, str])
async def get_mode(engine: DGEngine = Depends(get_dg_engine)):
    """Récupère le mode de fonctionnement actuel."""
    return {"mode": engine.mode.name}

@router.post("/mode/{mode}", response_model=Dict[str, str])
async def set_mode(mode: str, engine: DGEngine = Depends(get_dg_engine)):
    """Change le mode de fonctionnement du DG."""
    try:
        mode_enum = DGMode[mode.upper()]
        engine.set_mode(mode_enum)
        return {"status": "success", "mode": mode_enum.name}
    except KeyError:
        valid_modes = [m.name.lower() for m in DGMode]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mode invalide. Valeurs possibles: {', '.join(valid_modes)}"
        )

# ========== DÉCISIONS (READ ONLY V1) ==========

@router.get("/decisions", response_model=List[Dict[str, Any]])
async def list_decisions(limit: int = 100):
    """[TODO] Liste les décisions prises par le DG."""
    return []  # À brancher sur la persistence

@router.get("/decisions/{decision_id}", response_model=Decision)
async def get_decision(decision_id: str):
    """[TODO] Détail d'une décision."""
    raise HTTPException(status_code=501, detail="Non implémenté")

@router.post("/decisions/{decision_id}/approve", response_model=Decision)
async def approve_decision(decision_id: str, approved_by: str, comment: Optional[str] = None):
    """[TODO] Approuve une décision."""
    raise HTTPException(status_code=501, detail="Non implémenté")

@router.post("/decisions/{decision_id}/reject", response_model=Decision)
async def reject_decision(decision_id: str, reason: str, rejected_by: str):
    """[TODO] Rejette une décision."""
    raise HTTPException(status_code=501, detail="Non implémenté")

# ========== ACTIONS (READ ONLY V1) ==========

@router.get("/actions", response_model=List[Dict[str, Any]])
async def list_actions(limit: int = 100):
    """[TODO] Liste les actions effectuées par le DG."""
    return []  # À brancher sur la persistence

@router.get("/actions/{action_id}", response_model=Action)
async def get_action(action_id: str):
    """[TODO] Détail d'une action spécifique."""
    raise HTTPException(status_code=501, detail="Non implémenté")

# ========== ALGORITHMES ==========

@router.get("/algorithms", response_model=Dict[str, Any])
async def list_algorithms(engine: DGEngine = Depends(get_dg_engine)):
    """Liste les algorithmes disponibles et leur statut."""
    return engine.strategy_engine.get_algorithm_status()

@router.post("/algorithms/{algorithm_name}/activate", response_model=Dict[str, Any])
async def activate_algorithm(algorithm_name: str, engine: DGEngine = Depends(get_dg_engine)):
    """Active un algorithme."""
    success = await engine.strategy_engine.activate_algorithm(algorithm_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Algorithme non trouvé: {algorithm_name}")
    return {"status": "success", "algorithm": algorithm_name, "active": True}

@router.post("/algorithms/{algorithm_name}/deactivate", response_model=Dict[str, Any])
async def deactivate_algorithm(algorithm_name: str, engine: DGEngine = Depends(get_dg_engine)):
    """Désactive un algorithme."""
    success = await engine.strategy_engine.deactivate_algorithm(algorithm_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Algorithme non trouvé: {algorithm_name}")
    return {"status": "success", "algorithm": algorithm_name, "active": False}

@router.post("/algorithms/{algorithm_name}/config", response_model=Dict[str, Any])
async def update_algorithm_config(
    algorithm_name: str,
    update: AlgorithmConfigUpdate,
    engine: DGEngine = Depends(get_dg_engine),
):
    """Met à jour la configuration d'un algorithme."""
    success = await engine.strategy_engine.update_algorithm_config(algorithm_name, update.config)
    if not success:
        raise HTTPException(status_code=404, detail=f"Algorithme non trouvé: {algorithm_name}")
    return {"status": "success", "algorithm": algorithm_name, "config_updated": True}

# ========== ANALYSE DG ==========

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_context(context: Dict[str, Any], engine: DGEngine = Depends(get_dg_engine)):
    """Soumet un contexte d'analyse et retourne des recommandations."""
    try:
        decision_context = await engine.analyze(context)
        return {
            "recommendations": [
                action.dict() for action in decision_context.recommended_actions
            ],
            "confidence": decision_context.confidence,
            "timestamp": decision_context.timestamp.isoformat(),
            "metadata": getattr(decision_context, "metadata", {}),
        }
    except Exception as e:
        _logger.error(f"Erreur lors de l'analyse: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse: {str(e)}"
        )

# ========== BOOTSTRAP DG + IA SUR APP ==========

def setup_dg_api(app, dg_engine: DGEngine):
    """
    Configure l'API du DG autonome avec intégration IA Supervisor.
    
    - Attache le DGEngine à app.state
    - Configure les routers DG (/api/dg) et IA (/api/ia)
    - Initialise l'IA Supervisor
    """
    # Configuration DG classique
    app.state.dg_engine = dg_engine
    app.include_router(router)
    _logger.info("API DG autonome configurée (router /api/dg)")
    
    # Configuration IA Supervisor
    try:
        init_ia_supervisor()
        
        # Import et enregistrement des routes IA
        from .router import router as ia_router
        app.include_router(ia_router)
        _logger.info("API IA Supervisor configurée (router /api/ia)")
        
    except Exception as e:
        _logger.error(f"Erreur configuration IA Supervisor: {e}")
        # Continue sans IA en mode dégradé
        _logger.warning("IA Supervisor indisponible, fonctionnement en mode DG seul")
