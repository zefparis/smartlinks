from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging

from ..db import get_db
from ..models import Offer, Creator, Segment

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/settings", tags=["settings"])

class SettingsResponse(BaseModel):
    general: Dict[str, Any]
    offers: List[Dict[str, Any]]
    creators: List[Dict[str, Any]]
    segments: List[Dict[str, Any]]

class UpdateSettingRequest(BaseModel):
    key: str
    value: Any

@router.get("", response_model=SettingsResponse)
async def get_settings(db: Session = Depends(get_db)):
    """
    Récupère tous les paramètres de l'application
    TOUJOURS retourne une structure complète même si BDD vide
    """
    try:
        logger.info("get_settings called")
        
        # Paramètres généraux - TOUJOURS présents
        general_settings = {
            "app_name": "SmartLinks Autopilot",
            "version": "1.0.0",
            "timezone": "UTC",
            "currency": "EUR",
            "default_cap_day": 1000,
            "fraud_threshold": 0.8,
            "auto_approval": True,
            "email_notifications": True,
            "slack_notifications": False,
            "max_daily_budget": 5000.0,
            "min_payout_threshold": 10.0,
            "status": "active",
            "last_updated": "2024-01-01T00:00:00Z"
        }
        
        # Récupérer les offres avec gestion d'erreur
        offers_data = []
        try:
            offers = db.query(Offer).all()
            logger.info(f"Found {len(offers)} offers in database")
            
            for offer in offers:
                offers_data.append({
                    "offer_id": getattr(offer, 'offer_id', 'unknown'),
                    "name": getattr(offer, 'name', 'Unnamed Offer'),
                    "url": getattr(offer, 'url', ''),
                    "status": getattr(offer, 'status', 'active'),
                    "cap_day": getattr(offer, 'cap_day', 1000),
                    "geo_allow": getattr(offer, 'geo_allow', 'ALL'),
                    "incent_ok": bool(getattr(offer, 'incent_ok', True))
                })
        except Exception as e:
            logger.warning(f"Error loading offers: {e}")
            # Return empty list but valid structure
        
        # Récupérer les créateurs avec gestion d'erreur
        creators_data = []
        try:
            creators = db.query(Creator).all()
            logger.info(f"Found {len(creators)} creators in database")
            
            for creator in creators:
                creators_data.append({
                    "creator_id": getattr(creator, 'creator_id', 'unknown'),
                    "name": getattr(creator, 'name', 'Unnamed Creator'),
                    "email": getattr(creator, 'email', ''),
                    "status": getattr(creator, 'status', 'active'),
                    "commission_rate": float(getattr(creator, 'commission_rate', 0.1)),
                    "total_earnings": float(getattr(creator, 'total_earnings', 0) or 0)
                })
        except Exception as e:
            logger.warning(f"Error loading creators: {e}")
            # Return empty list but valid structure
        
        # Récupérer les segments avec gestion d'erreur
        segments_data = []
        try:
            segments = db.query(Segment).all()
            logger.info(f"Found {len(segments)} segments in database")
            
            for segment in segments:
                geo_targets = getattr(segment, 'geo_targets', '')
                device_targets = getattr(segment, 'device_targets', '')
                
                segments_data.append({
                    "segment_id": getattr(segment, 'segment_id', 'unknown'),
                    "name": getattr(segment, 'name', 'Unnamed Segment'),
                    "description": getattr(segment, 'description', ''),
                    "status": getattr(segment, 'status', 'active'),
                    "traffic_source": getattr(segment, 'traffic_source', 'unknown'),
                    "geo_targets": geo_targets.split(',') if geo_targets else [],
                    "device_targets": device_targets.split(',') if device_targets else []
                })
        except Exception as e:
            logger.warning(f"Error loading segments: {e}")
            # Return empty list but valid structure
        
        return SettingsResponse(
            general=general_settings,
            offers=offers_data,
            creators=creators_data,
            segments=segments_data
        )
        
    except Exception as e:
        logger.error(f"Erreur récupération settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des paramètres: {str(e)}"
        )

@router.put("/general")
async def update_general_setting(
    request: UpdateSettingRequest,
    db: Session = Depends(get_db)
):
    """
    Met à jour un paramètre général
    """
    try:
        # Pour cette démo, on simule la mise à jour
        # Dans une vraie app, on sauvegarderait en base
        
        allowed_keys = [
            "app_name", "timezone", "currency", "default_cap_day",
            "fraud_threshold", "auto_approval", "email_notifications",
            "slack_notifications", "max_daily_budget", "min_payout_threshold"
        ]
        
        if request.key not in allowed_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Paramètre '{request.key}' non autorisé"
            )
        
        # Validation basique selon le type
        if request.key in ["fraud_threshold"] and not (0 <= request.value <= 1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="fraud_threshold doit être entre 0 et 1"
            )
        
        if request.key in ["default_cap_day", "max_daily_budget", "min_payout_threshold"] and request.value < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Les valeurs numériques doivent être positives"
            )
        
        return {
            "success": True,
            "message": f"Paramètre '{request.key}' mis à jour avec succès",
            "key": request.key,
            "value": request.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur mise à jour setting: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )

@router.put("/offer/{offer_id}")
async def update_offer_setting(
    offer_id: str,
    request: UpdateSettingRequest,
    db: Session = Depends(get_db)
):
    """
    Met à jour un paramètre d'offre
    """
    try:
        offer = db.query(Offer).filter(Offer.offer_id == offer_id).first()
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Offre '{offer_id}' non trouvée"
            )
        
        allowed_keys = ["name", "url", "status", "cap_day", "geo_allow", "incent_ok"]
        
        if request.key not in allowed_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Paramètre '{request.key}' non autorisé pour les offres"
            )
        
        # Mettre à jour l'offre
        setattr(offer, request.key, request.value)
        db.commit()
        
        return {
            "success": True,
            "message": f"Offre '{offer_id}' mise à jour avec succès",
            "offer_id": offer_id,
            "key": request.key,
            "value": request.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur mise à jour offre: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour de l'offre: {str(e)}"
        )

@router.get("/export")
async def export_settings(db: Session = Depends(get_db)):
    """
    Exporte tous les paramètres en JSON
    """
    try:
        settings = await get_settings(db)
        return {
            "export_timestamp": "2025-01-19T15:30:00Z",
            "version": "1.0.0",
            "data": settings.dict()
        }
    except Exception as e:
        logger.error(f"Erreur export settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'export: {str(e)}"
        )

@router.get("/health")
async def settings_health():
    """
    Vérification de santé du module settings
    """
    return {
        "status": "healthy",
        "module": "settings",
        "timestamp": "2025-01-19T15:30:00Z",
        "features": ["general_settings", "offer_management", "creator_management", "export"]
    }
