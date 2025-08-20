"""Webhooks API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Dict, List, Any, Optional
from datetime import datetime

from .service import WebhookService, WebhookConfig, WebhookType, EventType, WebhookEvent
from ..observability.otel import trace_function

router = APIRouter()

# Global webhook service
webhook_service = WebhookService()

def check_role(x_role: str = Header(None)):
    """Check user role for RBAC."""
    if not x_role or x_role not in ["viewer", "operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Invalid or missing role")
    return x_role

@router.post("/webhooks")
@trace_function("api.webhooks.register")
async def register_webhook(
    config: Dict[str, Any],
    role: str = Depends(check_role)
):
    """Register a new webhook."""
    if role not in ["admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    webhook_config = WebhookConfig(
        id=config["id"],
        name=config["name"],
        webhook_type=WebhookType(config["webhook_type"]),
        url=config["url"],
        events=[EventType(e) for e in config["events"]],
        headers=config.get("headers", {}),
        template=config.get("template"),
        enabled=config.get("enabled", True),
        retry_count=config.get("retry_count", 3),
        timeout_seconds=config.get("timeout_seconds", 10)
    )
    
    webhook_service.register_webhook(webhook_config)
    return {"status": "registered", "webhook_id": config["id"]}

@router.delete("/webhooks/{webhook_id}")
@trace_function("api.webhooks.unregister")
async def unregister_webhook(
    webhook_id: str,
    role: str = Depends(check_role)
):
    """Unregister a webhook."""
    if role not in ["admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    webhook_service.unregister_webhook(webhook_id)
    return {"status": "unregistered", "webhook_id": webhook_id}

@router.get("/webhooks")
async def list_webhooks(role: str = Depends(check_role)):
    """List registered webhooks."""
    webhooks = []
    for webhook_id, config in webhook_service.webhooks.items():
        webhooks.append({
            "id": config.id,
            "name": config.name,
            "webhook_type": config.webhook_type.value,
            "url": config.url,
            "events": [e.value for e in config.events],
            "enabled": config.enabled
        })
    return {"webhooks": webhooks}

@router.post("/webhooks/test")
@trace_function("api.webhooks.test")
async def test_webhook(
    webhook_id: str,
    test_event: Dict[str, Any],
    role: str = Depends(check_role)
):
    """Test a webhook with a sample event."""
    if role not in ["admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if webhook_id not in webhook_service.webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    event = WebhookEvent(
        event_type=EventType(test_event["event_type"]),
        timestamp=datetime.utcnow(),
        source="test",
        severity=test_event.get("severity", "info"),
        data=test_event.get("data", {})
    )
    
    await webhook_service.send_event(event)
    return {"status": "test_sent", "webhook_id": webhook_id}

@router.get("/webhooks/types")
async def list_webhook_types(role: str = Depends(check_role)):
    """List available webhook types and events."""
    return {
        "webhook_types": [
            {"value": "slack", "description": "Slack integration"},
            {"value": "jira", "description": "Jira issue creation"},
            {"value": "pagerduty", "description": "PagerDuty alerting"},
            {"value": "generic", "description": "Generic HTTP webhook"}
        ],
        "event_types": [
            {"value": "policy_violation", "description": "RCP policy violation"},
            {"value": "rollback_triggered", "description": "Policy rollback triggered"},
            {"value": "approval_required", "description": "Approval required"},
            {"value": "system_alert", "description": "System alert"},
            {"value": "performance_anomaly", "description": "Performance anomaly detected"}
        ]
    }
