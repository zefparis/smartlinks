"""
Health Router - Provides health check endpoints for the SmartLinks API.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

# Set up logging
logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

@router.get(
    "/health",
    response_model=Dict[str, str],
    responses={
        200: {
            "description": "API is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "service": "SmartLinks API",
                        "timestamp": "2025-08-18T16:30:00Z"
                    }
                }
            }
        }
    }
)
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    
    Returns:
        Dict containing service status and timestamp
    """
    response = {
        "status": "ok",
        "service": "SmartLinks API",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    logger.debug(f"Health check: {response}")
    return response
