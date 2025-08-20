"""Webhooks service for external integrations (Slack/Jira/PagerDuty)."""

import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from ..observability.otel import trace_function

class WebhookType(Enum):
    SLACK = "slack"
    JIRA = "jira"
    PAGERDUTY = "pagerduty"
    GENERIC = "generic"

class EventType(Enum):
    POLICY_VIOLATION = "policy_violation"
    ROLLBACK_TRIGGERED = "rollback_triggered"
    APPROVAL_REQUIRED = "approval_required"
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE_ANOMALY = "performance_anomaly"

@dataclass
class WebhookConfig:
    """Webhook configuration."""
    id: str
    name: str
    webhook_type: WebhookType
    url: str
    events: List[EventType]
    headers: Dict[str, str]
    template: Optional[str] = None
    enabled: bool = True
    retry_count: int = 3
    timeout_seconds: int = 10

@dataclass
class WebhookEvent:
    """Webhook event data."""
    event_type: EventType
    timestamp: datetime
    source: str
    data: Dict[str, Any]
    severity: str = "info"
    tenant_id: Optional[str] = None

class SlackFormatter:
    """Slack message formatter."""
    
    @staticmethod
    def format_policy_violation(event: WebhookEvent) -> Dict[str, Any]:
        """Format policy violation for Slack."""
        data = event.data
        
        color = "danger" if event.severity == "critical" else "warning"
        
        return {
            "attachments": [
                {
                    "color": color,
                    "title": "🚨 Policy Violation Detected",
                    "fields": [
                        {
                            "title": "Policy",
                            "value": data.get("policy_name", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Algorithm",
                            "value": data.get("algo_key", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Action Blocked",
                            "value": data.get("blocked_action", "Unknown"),
                            "short": False
                        },
                        {
                            "title": "Risk Cost",
                            "value": f"${data.get('risk_cost', 0):.2f}",
                            "short": True
                        }
                    ],
                    "footer": "SmartLinks Autopilot",
                    "ts": int(event.timestamp.timestamp())
                }
            ]
        }
    
    @staticmethod
    def format_rollback(event: WebhookEvent) -> Dict[str, Any]:
        """Format rollback event for Slack."""
        data = event.data
        
        return {
            "attachments": [
                {
                    "color": "danger",
                    "title": "🔄 Policy Rollback Triggered",
                    "fields": [
                        {
                            "title": "Policy",
                            "value": data.get("policy_id", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Reason",
                            "value": data.get("reason", "SLO violation"),
                            "short": True
                        },
                        {
                            "title": "Metric Violated",
                            "value": data.get("violated_metric", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Threshold",
                            "value": str(data.get("threshold", "Unknown")),
                            "short": True
                        }
                    ],
                    "footer": "SmartLinks Autopilot",
                    "ts": int(event.timestamp.timestamp())
                }
            ]
        }
    
    @staticmethod
    def format_approval_required(event: WebhookEvent) -> Dict[str, Any]:
        """Format approval required for Slack."""
        data = event.data
        
        return {
            "attachments": [
                {
                    "color": "warning",
                    "title": "✋ Approval Required",
                    "fields": [
                        {
                            "title": "Change Type",
                            "value": data.get("change_type", "Policy Change"),
                            "short": True
                        },
                        {
                            "title": "Requested By",
                            "value": data.get("requested_by", "System"),
                            "short": True
                        },
                        {
                            "title": "Risk Level",
                            "value": data.get("risk_level", "Medium"),
                            "short": True
                        },
                        {
                            "title": "Approval URL",
                            "value": data.get("approval_url", "#"),
                            "short": False
                        }
                    ],
                    "footer": "SmartLinks Autopilot",
                    "ts": int(event.timestamp.timestamp())
                }
            ]
        }

class JiraFormatter:
    """Jira issue formatter."""
    
    @staticmethod
    def format_policy_violation(event: WebhookEvent) -> Dict[str, Any]:
        """Format policy violation as Jira issue."""
        data = event.data
        
        return {
            "fields": {
                "project": {"key": data.get("jira_project", "SMARTLINKS")},
                "summary": f"Policy Violation: {data.get('policy_name', 'Unknown')}",
                "description": f"""
Policy violation detected in SmartLinks Autopilot:

*Policy:* {data.get('policy_name', 'Unknown')}
*Algorithm:* {data.get('algo_key', 'Unknown')}
*Action Blocked:* {data.get('blocked_action', 'Unknown')}
*Risk Cost:* ${data.get('risk_cost', 0):.2f}
*Timestamp:* {event.timestamp.isoformat()}

Please review and take appropriate action.
                """.strip(),
                "issuetype": {"name": "Bug"},
                "priority": {"name": "High" if event.severity == "critical" else "Medium"},
                "labels": ["autopilot", "policy-violation", "automated"]
            }
        }

class PagerDutyFormatter:
    """PagerDuty event formatter."""
    
    @staticmethod
    def format_system_alert(event: WebhookEvent) -> Dict[str, Any]:
        """Format system alert for PagerDuty."""
        data = event.data
        
        return {
            "routing_key": data.get("routing_key", ""),
            "event_action": "trigger",
            "dedup_key": f"smartlinks-{event.source}-{data.get('alert_id', 'unknown')}",
            "payload": {
                "summary": data.get("summary", "SmartLinks Autopilot Alert"),
                "source": event.source,
                "severity": event.severity,
                "timestamp": event.timestamp.isoformat(),
                "component": "smartlinks-autopilot",
                "group": "autopilot",
                "class": data.get("alert_class", "system"),
                "custom_details": data
            }
        }

class WebhookService:
    """Webhook service for external integrations."""
    
    def __init__(self):
        self.webhooks: Dict[str, WebhookConfig] = {}
        self.formatters = {
            WebhookType.SLACK: SlackFormatter(),
            WebhookType.JIRA: JiraFormatter(),
            WebhookType.PAGERDUTY: PagerDutyFormatter()
        }
    
    def register_webhook(self, config: WebhookConfig):
        """Register a new webhook."""
        self.webhooks[config.id] = config
    
    def unregister_webhook(self, webhook_id: str):
        """Unregister a webhook."""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
    
    @trace_function("webhooks.send_event")
    async def send_event(self, event: WebhookEvent):
        """Send event to all applicable webhooks."""
        
        tasks = []
        for webhook in self.webhooks.values():
            if (webhook.enabled and 
                event.event_type in webhook.events and
                self._should_send_to_webhook(webhook, event)):
                
                task = asyncio.create_task(
                    self._send_to_webhook(webhook, event)
                )
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_to_webhook(self, webhook: WebhookConfig, event: WebhookEvent):
        """Send event to a specific webhook."""
        
        try:
            # Format payload based on webhook type
            payload = self._format_payload(webhook, event)
            
            # Send HTTP request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook.url,
                    json=payload,
                    headers=webhook.headers,
                    timeout=aiohttp.ClientTimeout(total=webhook.timeout_seconds)
                ) as response:
                    
                    if response.status >= 400:
                        print(f"Webhook {webhook.id} failed: {response.status} {await response.text()}")
                    else:
                        print(f"Webhook {webhook.id} sent successfully")
        
        except Exception as e:
            print(f"Error sending webhook {webhook.id}: {str(e)}")
            # Could implement retry logic here
    
    def _format_payload(self, webhook: WebhookConfig, event: WebhookEvent) -> Dict[str, Any]:
        """Format event payload for webhook type."""
        
        formatter = self.formatters.get(webhook.webhook_type)
        
        if webhook.webhook_type == WebhookType.SLACK:
            if event.event_type == EventType.POLICY_VIOLATION:
                return formatter.format_policy_violation(event)
            elif event.event_type == EventType.ROLLBACK_TRIGGERED:
                return formatter.format_rollback(event)
            elif event.event_type == EventType.APPROVAL_REQUIRED:
                return formatter.format_approval_required(event)
        
        elif webhook.webhook_type == WebhookType.JIRA:
            if event.event_type == EventType.POLICY_VIOLATION:
                return formatter.format_policy_violation(event)
        
        elif webhook.webhook_type == WebhookType.PAGERDUTY:
            if event.event_type == EventType.SYSTEM_ALERT:
                return formatter.format_system_alert(event)
        
        # Generic fallback
        return {
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source,
            "severity": event.severity,
            "data": event.data,
            "tenant_id": event.tenant_id
        }
    
    def _should_send_to_webhook(self, webhook: WebhookConfig, event: WebhookEvent) -> bool:
        """Determine if event should be sent to webhook."""
        
        # Could implement filtering logic here
        # e.g., severity thresholds, tenant filtering, rate limiting
        
        return True

# Global webhook service instance
webhook_service = WebhookService()

# Convenience functions for common events
async def send_policy_violation_alert(policy_name: str, algo_key: str, 
                                    blocked_action: str, risk_cost: float,
                                    severity: str = "warning"):
    """Send policy violation alert."""
    event = WebhookEvent(
        event_type=EventType.POLICY_VIOLATION,
        timestamp=datetime.utcnow(),
        source="rcp_evaluator",
        severity=severity,
        data={
            "policy_name": policy_name,
            "algo_key": algo_key,
            "blocked_action": blocked_action,
            "risk_cost": risk_cost
        }
    )
    await webhook_service.send_event(event)

async def send_rollback_alert(policy_id: str, reason: str, violated_metric: str, 
                            threshold: float, severity: str = "critical"):
    """Send rollback alert."""
    event = WebhookEvent(
        event_type=EventType.ROLLBACK_TRIGGERED,
        timestamp=datetime.utcnow(),
        source="canary_monitor",
        severity=severity,
        data={
            "policy_id": policy_id,
            "reason": reason,
            "violated_metric": violated_metric,
            "threshold": threshold
        }
    )
    await webhook_service.send_event(event)

async def send_approval_request(change_type: str, requested_by: str, 
                              risk_level: str, approval_url: str):
    """Send approval request notification."""
    event = WebhookEvent(
        event_type=EventType.APPROVAL_REQUIRED,
        timestamp=datetime.utcnow(),
        source="approval_system",
        severity="info",
        data={
            "change_type": change_type,
            "requested_by": requested_by,
            "risk_level": risk_level,
            "approval_url": approval_url
        }
    )
    await webhook_service.send_event(event)

async def send_system_alert(summary: str, alert_id: str, alert_class: str = "system",
                          routing_key: str = "", severity: str = "warning"):
    """Send system alert to PagerDuty."""
    event = WebhookEvent(
        event_type=EventType.SYSTEM_ALERT,
        timestamp=datetime.utcnow(),
        source="system_monitor",
        severity=severity,
        data={
            "summary": summary,
            "alert_id": alert_id,
            "alert_class": alert_class,
            "routing_key": routing_key
        }
    )
    await webhook_service.send_event(event)
