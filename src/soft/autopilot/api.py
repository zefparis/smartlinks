"""FastAPI router for autopilot algorithm settings and AI governance."""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json
from datetime import datetime

from .models import AlgorithmSettings, AIPolicy, AuditSettings
from .schemas import (
    ALGORITHM_SETTINGS_MAP,
    AIPolicy as AIPolicySchema,
    AlgorithmSettingsResponse,
    AuditEntry,
    PreviewResponse,
    PreviewAction,
    AuthorityLevel
)
from ..dg.dependencies import get_db

router = APIRouter(prefix="/autopilot", tags=["autopilot"])


def get_user_role(x_role: str = Header(default="viewer")) -> str:
    """Simple RBAC based on X-Role header."""
    return x_role.lower()


def require_role(required_roles: List[str]):
    """Dependency to require specific roles."""
    def check_role(role: str = Depends(get_user_role)):
        if role not in required_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Required role: {required_roles}, got: {role}"
            )
        return role
    return check_role


@router.get("/algorithms")
async def list_algorithms(db: Session = Depends(get_db)):
    """List all algorithms with status and performance metrics."""
    algorithms = [
        {
            "key": "traffic_optimizer",
            "name": "Traffic Optimizer",
            "description": "Optimizes traffic routing based on CVR, revenue, or CTR",
            "status": "active",
            "last_run": "2025-08-20T01:30:00Z",
            "performance": {"actions_taken": 12, "improvement": "+2.3%"}
        },
        {
            "key": "anomaly_detector", 
            "name": "Anomaly Detector",
            "description": "Detects traffic anomalies and triggers mitigations",
            "status": "active",
            "last_run": "2025-08-20T01:25:00Z",
            "performance": {"alerts_sent": 3, "false_positives": "0.5%"}
        },
        {
            "key": "budget_arbitrage",
            "name": "Budget Arbitrage", 
            "description": "Reallocates budget based on performance and ROI",
            "status": "active",
            "last_run": "2025-08-20T01:20:00Z",
            "performance": {"budget_moved": "€1,250", "roi_improvement": "+8.1%"}
        },
        {
            "key": "predictive_alerting",
            "name": "Predictive Alerting",
            "description": "Predicts issues before they occur",
            "status": "active", 
            "last_run": "2025-08-20T01:15:00Z",
            "performance": {"predictions": 5, "accuracy": "87%"}
        },
        {
            "key": "self_healing",
            "name": "Self-Healing",
            "description": "Automatically fixes detected issues",
            "status": "active",
            "last_run": "2025-08-20T01:10:00Z", 
            "performance": {"fixes_applied": 2, "success_rate": "95%"}
        }
    ]
    return {"algorithms": algorithms}


@router.get("/algorithms/{algo_key}/settings")
async def get_algorithm_settings(
    algo_key: str,
    db: Session = Depends(get_db)
) -> AlgorithmSettingsResponse:
    """Get algorithm settings with schema and metadata."""
    if algo_key not in ALGORITHM_SETTINGS_MAP:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    
    # Get settings from database
    settings_record = db.query(AlgorithmSettings).filter(
        AlgorithmSettings.algo_key == algo_key
    ).first()
    
    settings_class = ALGORITHM_SETTINGS_MAP[algo_key]
    
    if settings_record:
        settings = settings_record.settings_json
        version = settings_record.version
        updated_by = settings_record.updated_by
        updated_at = settings_record.updated_at.isoformat()
    else:
        # Return defaults
        default_settings = settings_class()
        settings = default_settings.dict()
        version = 0
        updated_by = "system"
        updated_at = datetime.now().isoformat()
    
    # Generate JSON schema
    schema = settings_class.schema()
    
    return AlgorithmSettingsResponse(
        settings=settings,
        schema=schema,
        version=version,
        updated_by=updated_by,
        updated_at=updated_at
    )


@router.put("/algorithms/{algo_key}/settings")
async def update_algorithm_settings(
    algo_key: str,
    settings_data: Dict[str, Any],
    db: Session = Depends(get_db),
    role: str = Depends(require_role(["admin", "dg_ai"]))
):
    """Update algorithm settings with validation and audit."""
    if algo_key not in ALGORITHM_SETTINGS_MAP:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    
    settings_class = ALGORITHM_SETTINGS_MAP[algo_key]
    
    # Validate settings
    try:
        validated_settings = settings_class(**settings_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid settings: {str(e)}")
    
    # Get current settings for audit
    current_record = db.query(AlgorithmSettings).filter(
        AlgorithmSettings.algo_key == algo_key
    ).first()
    
    current_settings = current_record.settings_json if current_record else {}
    new_settings = validated_settings.dict()
    
    # Calculate diff for audit
    diff = {
        "before": current_settings,
        "after": new_settings,
        "changed_fields": []
    }
    
    for key, new_value in new_settings.items():
        if key not in current_settings or current_settings[key] != new_value:
            diff["changed_fields"].append({
                "field": key,
                "old": current_settings.get(key),
                "new": new_value
            })
    
    # Update or create settings
    if current_record:
        current_record.settings_json = new_settings
        current_record.version += 1
        current_record.updated_by = role
        current_record.updated_at = datetime.now()
    else:
        current_record = AlgorithmSettings(
            algo_key=algo_key,
            settings_json=new_settings,
            version=1,
            updated_by=role,
            updated_at=datetime.now()
        )
        db.add(current_record)
    
    # Create audit entry
    audit_entry = AuditSettings(
        algo_key=algo_key,
        actor=role,
        diff_json=diff,
        created_at=datetime.now()
    )
    db.add(audit_entry)
    
    db.commit()
    
    return {
        "message": "Settings updated successfully",
        "version": current_record.version,
        "changes": len(diff["changed_fields"])
    }


@router.get("/ai/policy/{algo_key}")
async def get_ai_policy(
    algo_key: str,
    db: Session = Depends(get_db)
) -> AIPolicySchema:
    """Get AI policy for algorithm or global."""
    policy_record = db.query(AIPolicy).filter(
        AIPolicy.algo_key == algo_key
    ).first()
    
    if policy_record:
        return AIPolicySchema(
            authority=policy_record.authority,
            risk_budget_daily=policy_record.risk_budget_daily,
            dry_run=policy_record.dry_run,
            hard_guards=policy_record.hard_guards_json,
            soft_guards=policy_record.soft_guards_json
        )
    else:
        # Return defaults
        return AIPolicySchema()


@router.put("/ai/policy/{algo_key}")
async def update_ai_policy(
    algo_key: str,
    policy_data: AIPolicySchema,
    db: Session = Depends(get_db),
    role: str = Depends(require_role(["dg_ai"]))
):
    """Update AI policy (requires dg_ai role)."""
    policy_record = db.query(AIPolicy).filter(
        AIPolicy.algo_key == algo_key
    ).first()
    
    if policy_record:
        policy_record.authority = policy_data.authority
        policy_record.risk_budget_daily = policy_data.risk_budget_daily
        policy_record.dry_run = policy_data.dry_run
        policy_record.hard_guards_json = policy_data.hard_guards
        policy_record.soft_guards_json = policy_data.soft_guards
        policy_record.updated_by = role
        policy_record.updated_at = datetime.now()
    else:
        policy_record = AIPolicy(
            algo_key=algo_key,
            authority=policy_data.authority,
            risk_budget_daily=policy_data.risk_budget_daily,
            dry_run=policy_data.dry_run,
            hard_guards_json=policy_data.hard_guards,
            soft_guards_json=policy_data.soft_guards,
            updated_by=role,
            updated_at=datetime.now()
        )
        db.add(policy_record)
    
    db.commit()
    
    return {"message": "AI policy updated successfully"}


@router.post("/algorithms/{algo_key}/run")
async def trigger_algorithm_run(
    algo_key: str,
    db: Session = Depends(get_db),
    role: str = Depends(require_role(["admin", "dg_ai"]))
):
    """Manually trigger algorithm run."""
    if algo_key not in ALGORITHM_SETTINGS_MAP:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    
    # In a real implementation, this would trigger the actual algorithm
    # For now, return a mock response
    return {
        "message": f"Algorithm {algo_key} run triggered",
        "run_id": f"run_{algo_key}_{int(datetime.now().timestamp())}",
        "status": "queued"
    }


@router.post("/algorithms/{algo_key}/override")
async def apply_manual_override(
    algo_key: str,
    override_data: Dict[str, Any],
    db: Session = Depends(get_db),
    role: str = Depends(require_role(["operator", "admin"]))
):
    """Apply manual override (doesn't change settings)."""
    if algo_key not in ALGORITHM_SETTINGS_MAP:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    
    # Log the override for audit
    audit_entry = AuditSettings(
        algo_key=algo_key,
        actor=role,
        diff_json={
            "type": "manual_override",
            "override_data": override_data,
            "timestamp": datetime.now().isoformat()
        },
        created_at=datetime.now()
    )
    db.add(audit_entry)
    db.commit()
    
    return {
        "message": f"Manual override applied to {algo_key}",
        "override_id": f"override_{algo_key}_{int(datetime.now().timestamp())}"
    }


@router.get("/algorithms/{algo_key}/preview")
async def preview_algorithm_run(
    algo_key: str,
    db: Session = Depends(get_db)
) -> PreviewResponse:
    """Preview algorithm actions without executing."""
    if algo_key not in ALGORITHM_SETTINGS_MAP:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    
    # Mock preview data - in real implementation, this would run the algorithm in dry-run mode
    mock_actions = [
        PreviewAction(
            action_type="reweight",
            target="destination_123",
            current_value=0.25,
            proposed_value=0.30,
            risk_score=0.2,
            justification="CVR improvement detected (+15%)"
        ),
        PreviewAction(
            action_type="budget_shift",
            target="campaign_456", 
            current_value=1000.0,
            proposed_value=1200.0,
            risk_score=0.3,
            justification="ROI above target, increasing allocation"
        )
    ]
    
    return PreviewResponse(
        actions=mock_actions,
        total_risk_score=0.5,
        estimated_impact={
            "cvr_change": "+2.1%",
            "revenue_change": "+€450/day",
            "confidence": "85%"
        },
        warnings=["High traffic period detected", "Limited historical data for destination_789"]
    )


@router.get("/audit/{algo_key}")
async def get_audit_history(
    algo_key: str,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> List[AuditEntry]:
    """Get audit history for algorithm settings."""
    audit_records = db.query(AuditSettings).filter(
        AuditSettings.algo_key == algo_key
    ).order_by(desc(AuditSettings.created_at)).limit(limit).all()
    
    return [
        AuditEntry(
            id=record.id,
            algo_key=record.algo_key,
            actor=record.actor,
            diff_json=record.diff_json,
            created_at=record.created_at.isoformat()
        )
        for record in audit_records
    ]
