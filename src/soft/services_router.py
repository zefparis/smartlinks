from datetime import datetime
from enum import Enum
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel
import subprocess
import psutil
import os

router = APIRouter(
    prefix="/api/services",
    tags=["services"],
    responses={404: {"description": "Not found"}},
)

class ServiceStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"

class ServiceInfo(BaseModel):
    status: ServiceStatus
    last_updated: str
    pid: Optional[int] = None
    error: Optional[str] = None

class ServicesStatusResponse(BaseModel):
    router: ServiceInfo
    autopilot: ServiceInfo
    probes: ServiceInfo

class ServiceActionResponse(BaseModel):
    success: bool
    service: str
    message: str
    status: ServiceStatus

class ServiceManager:
    _instance = None
    _services = {
        "router": {
            "process": None,
            "status": ServiceStatus.STOPPED,
            "last_updated": datetime.utcnow().isoformat(),
            "command": ["python", "-m", "src.soft.router"],
            "port": 8000
        },
        "autopilot": {
            "process": None,
            "status": ServiceStatus.STOPPED,
            "last_updated": datetime.utcnow().isoformat(),
            "command": ["python", "-m", "src.soft.autopilot"],
            "port": 8001
        },
        "probes": {
            "process": None,
            "status": ServiceStatus.STOPPED,
            "last_updated": datetime.utcnow().isoformat(),
            "command": ["python", "-m", "src.soft.probes"],
            "port": 8002
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceManager, cls).__new__(cls)
            cls._instance._check_existing_processes()
        return cls._instance

    def _check_existing_processes(self):
        for service_name, service in self._services.items():
            if service["process"] and service["process"].poll() is None:
                service["status"] = ServiceStatus.RUNNING
            else:
                service["status"] = ServiceStatus.STOPPED
                service["process"] = None
            service["last_updated"] = datetime.utcnow().isoformat()

    def get_status(self, service_name: str) -> Dict[str, Any]:
        service = self._services.get(service_name)
        if not service:
            return None
            
        # Check if process is still running
        if service["status"] == ServiceStatus.RUNNING and service["process"] and service["process"].poll() is not None:
            service["status"] = ServiceStatus.STOPPED
            service["process"] = None
            service["last_updated"] = datetime.utcnow().isoformat()
            
        return {
            "status": service["status"],
            "last_updated": service["last_updated"],
            "pid": service["process"].pid if service["process"] else None
        }

    def start_service(self, service_name: str) -> Dict[str, Any]:
        service = self._services.get(service_name)
        if not service:
            return {"success": False, "message": f"Service {service_name} not found"}
            
        if service["status"] == ServiceStatus.RUNNING:
            return {"success": True, "message": f"{service_name} is already running"}

        try:
            service["status"] = ServiceStatus.STARTING
            service["last_updated"] = datetime.utcnow().isoformat()
            
            # Start the service in a new process group
            service["process"] = subprocess.Popen(
                service["command"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            service["status"] = ServiceStatus.RUNNING
            service["last_updated"] = datetime.utcnow().isoformat()
            return {"success": True, "message": f"{service_name} started successfully"}
            
        except Exception as e:
            service["status"] = ServiceStatus.ERROR
            service["last_updated"] = datetime.utcnow().isoformat()
            return {"success": False, "message": f"Failed to start {service_name}: {str(e)}"}

    def stop_service(self, service_name: str) -> Dict[str, Any]:
        service = self._services.get(service_name)
        if not service:
            return {"success": False, "message": f"Service {service_name} not found"}
            
        if service["status"] != ServiceStatus.RUNNING or not service["process"]:
            return {"success": True, "message": f"{service_name} is not running"}

        try:
            service["status"] = ServiceStatus.STOPPING
            service["last_updated"] = datetime.utcnow().isoformat()
            
            # Terminate the process group
            process = psutil.Process(service["process"].pid)
            for proc in process.children(recursive=True):
                proc.terminate()
            process.terminate()
            
            service["process"] = None
            service["status"] = ServiceStatus.STOPPED
            service["last_updated"] = datetime.utcnow().isoformat()
            return {"success": True, "message": f"{service_name} stopped successfully"}
            
        except Exception as e:
            service["status"] = ServiceStatus.ERROR
            service["last_updated"] = datetime.utcnow().isoformat()
            return {"success": False, "message": f"Failed to stop {service_name}: {str(e)}"}

# Initialize service manager
service_manager = ServiceManager()

@router.get("/status")
async def get_services_status():
    """
    Get the current status of all services
    Returns a simplified status object that matches frontend expectations
    """
    router_status = service_manager.get_status("router")
    autopilot_status = service_manager.get_status("autopilot")
    probes_status = service_manager.get_status("probes")
    
    # Return a simplified status object that matches frontend expectations
    return {
        "data": {
            "router": router_status["status"] == ServiceStatus.RUNNING if router_status else False,
            "autopilot": autopilot_status["status"] == ServiceStatus.RUNNING if autopilot_status else False,
            "probes": probes_status["status"] == ServiceStatus.RUNNING if probes_status else False,
            "ts": datetime.utcnow().isoformat()
        }
    }

@router.post("/router/start")
async def start_router():
    """
    Start the router service
    """
    result = service_manager.start_service("router")
    status = service_manager.get_status("router")
    return {
        "success": result["success"],
        "message": result["message"],
        "status": status["status"].value if status else ServiceStatus.ERROR.value
    }

@router.post("/autopilot/start")
async def start_autopilot():
    """
    Start the autopilot service
    """
    result = service_manager.start_service("autopilot")
    status = service_manager.get_status("autopilot")
    return {
        "success": result["success"],
        "message": result["message"],
        "status": status["status"].value if status else ServiceStatus.ERROR.value
    }

@router.post("/probes/start")
async def start_probes():
    """
    Start the probes service
    """
    result = service_manager.start_service("probes")
    status = service_manager.get_status("probes")
    return {
        "success": result["success"],
        "message": result["message"],
        "status": status["status"].value if status else ServiceStatus.ERROR.value
    }

@router.post("/router/stop")
async def stop_router():
    """
    Stop the router service
    """
    result = service_manager.stop_service("router")
    status = service_manager.get_status("router")
    return {
        "success": result["success"],
        "message": result["message"],
        "status": status["status"].value if status else ServiceStatus.ERROR.value
    }

@router.post("/autopilot/stop")
async def stop_autopilot():
    """
    Stop the autopilot service
    """
    result = service_manager.stop_service("autopilot")
    status = service_manager.get_status("autopilot")
    return {
        "success": result["success"],
        "message": result["message"],
        "status": status["status"].value if status else ServiceStatus.ERROR.value
    }

@router.post("/probes/stop")
async def stop_probes():
    """
    Stop the probes service
    """
    result = service_manager.stop_service("probes")
    status = service_manager.get_status("probes")
    return {
        "success": result["success"],
        "message": result["message"],
        "status": status["status"].value if status else ServiceStatus.ERROR.value
    }
