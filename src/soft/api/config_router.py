from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from pydantic import BaseModel

router = APIRouter(prefix="/config", tags=["config"])

class ConfigResponse(BaseModel):
    app_name: str = "SmartLinks Autopilot"
    version: str = "1.0.0"
    features: list = ["analytics", "clicks", "conversions"]

@router.get("", response_model=ConfigResponse)
async def get_config():
    """
    Get application configuration and available features.
    """
    return ConfigResponse()
