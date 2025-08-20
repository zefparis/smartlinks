"""
Status Router - Provides system status and health check endpoints.
"""
import time
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Some system metrics will be unavailable.")

import platform
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
import logging
import socket

# Set up logging
logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])

# Track application start time
APP_START_TIME = time.time()

class SystemStatus:
    def __init__(self):
        self.start_time = time.time()
        self.hostname = socket.gethostname()
        self.platform = platform.system()
        self.platform_version = platform.version()
        self.python_version = platform.python_version()
        
    def get_uptime(self) -> Dict[str, Any]:
        """Get system and application uptime."""
        uptime_seconds = time.time() - self.start_time
        
        # Calculate days, hours, minutes, seconds
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            "days": int(days),
            "hours": int(hours),
            "minutes": int(minutes),
            "seconds": int(seconds),
            "total_seconds": int(uptime_seconds)
        }
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics if psutil is available."""
        if not PSUTIL_AVAILABLE:
            return {
                "cpu_percent": None,
                "memory_usage": None,
                "disk_usage": None,
                "warning": "psutil not available for detailed system metrics"
            }
            
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.5),
                "memory_usage": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent,
                    "used": psutil.virtual_memory().used,
                    "free": psutil.virtual_memory().free
                },
                "disk_usage": {
                    "total": psutil.disk_usage('/').total,
                    "used": psutil.disk_usage('/').used,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                }
            }
        except Exception as e:
            logger.warning(f"Error getting system metrics: {e}")
            return {
                "error": str(e),
                "warning": "Failed to get some system metrics"
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information."""
        try:
            return {
                "hostname": self.hostname,
                "os": f"{self.platform} {self.platform_version}",
                "python_version": self.python_version,
                "cpu_usage": f"{psutil.cpu_percent()}%",
                "memory_usage": f"{psutil.virtual_memory().percent}%",
                "disk_usage": f"{psutil.disk_usage('/').percent}%"
            }
        except Exception as e:
            logger.warning(f"Could not get system info: {e}")
            return {"error": "System information unavailable"}

# Global status instance
system_status = SystemStatus()

@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    Get system status and health information.
    
    Returns:
        Dict containing system status, uptime, and service health
    """
    try:
        # Get system information
        system_info = {
            "hostname": system_status.hostname,
            "platform": system_status.platform,
            "platform_version": system_status.platform_version,
            "python_version": system_status.python_version,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Get system metrics
        system_metrics = system_status.get_system_metrics()
        
        # Build status response
        status = {
            "status": "operational",
            "version": "1.0.0",
            "uptime": system_status.get_uptime(),
            "system": {
                **system_info,
                **system_metrics
            },
            "services": get_services_status()
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting system status: {str(e)}"
        )

@router.get("/status/services")
def get_services_status() -> Dict[str, Dict[str, str]]:
    """
    Get detailed status of all services.
    
    Returns:
        Dict mapping service names to their status information
    """
    return {
        "router": {
            "status": "running",
            "last_check": datetime.now(timezone.utc).isoformat()
        },
        "autopilot": {
            "status": "idle",
            "last_check": datetime.now(timezone.utc).isoformat()
        },
        "probes": {
            "status": "active",
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    }

@router.get("/status/health")
async def health_check() -> Dict[str, str]:
    """
    Simple health check endpoint.
    
    Returns:
        Basic health status
    """
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
