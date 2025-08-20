from fastapi import APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import func
import time

from .db import SessionLocal
from .models import Click, Conversion
from .storage import get_payout_rate

admin_router = APIRouter(prefix="/admin", tags=["admin"])

# --- helpers
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Endpoints

@admin_router.get("/health")
def health():
    """
    Vérifie la santé du stack (router + autopilot).
    Ici tu peux étendre pour checker Redis, MQ, etc.
    """
    return {
        "router": True,
        "autopilot": True,
        "ts": int(time.time())
    }

@admin_router.get("/metrics")
def metrics():
    """
    Statistiques globales sur les clics par segment
    """
    db: Session = next(db_session())

    clicks_total = db.query(func.count(Click.id)).scalar() or 0
    last_click = db.query(Click).order_by(Click.ts.desc()).first()

    segments = (
        db.query(
            Click.segment,
            func.count(Click.id).label("count"),
            func.avg(Click.risk).label("avg_risk")
        )
        .group_by(Click.segment)
        .all()
    )

    segs = [
        {"segment": s[0], "count": s[1], "avg_risk": round(s[2] or 0, 3)}
        for s in segments
    ]

    return {
        "clicks_total": clicks_total,
        "last_click_id": getattr(last_click, "click_id", None),
        "last_click_time": getattr(last_click, "ts", None),
        "segments": segs,
    }

@admin_router.get("/stats")
def stats():
    """
    Statistiques fraude + conversions
    """
    db: Session = next(db_session())

    fraud_suspects = db.query(func.count(Click.id)).filter(Click.risk > 0.5).scalar() or 0
    total_clicks = db.query(func.count(Click.id)).scalar() or 1
    fraud_rate = fraud_suspects / total_clicks

    approved = db.query(func.count(Conversion.id)).filter(Conversion.status == "approved").scalar() or 0
    total_conv = db.query(func.count(Conversion.id)).scalar() or 1
    approval_rate = approved / total_conv

    return {
        "fraud_suspects": fraud_suspects,
        "fraud_rate": round(fraud_rate, 3),
        "approved": approved,
        "approval_rate": round(approval_rate, 3),
    }

@admin_router.post("/seed")
def seed():
    """
    Simule quelques clics pour tester
    """
    from .simulate import seed_clicks
    seed_clicks()
    return {"ok": True, "msg": "DB seeded"}

@admin_router.post("/payout")
def payout():
    """
    Met à jour les taux de payout
    """
    payout_fr = get_payout_rate("FR:mobile")
    return {"ok": True, "msg": f"Payout FR:mobile = {payout_fr}"}

# Alias to match frontend expectation: POST /admin/payouts
@admin_router.post("/payouts")
def payouts_alias():
    return payout()

# Existing route (kept) and alias to match frontend: POST /admin/flush
@admin_router.post("/db/flush")
def flush():
    """
    Reset la DB (clics + conversions)
    """
    db: Session = next(db_session())
    db.query(Click).delete()
    db.query(Conversion).delete()
    db.commit()
    return {"ok": True, "msg": "DB flushed"}

@admin_router.post("/flush")
def flush_alias():
    return flush()

# ----------------------------
# Service control endpoints
# ----------------------------
_service_state = {
    "router": True,
    "autopilot": True,
    "probes": False,
}

@admin_router.get("/status")
def service_status():
    """Return current service states."""
    return _service_state

@admin_router.post("/service/{name}/start")
def service_start(name: str):
    if name not in _service_state:
        return {"ok": False, "error": f"unknown service '{name}'"}
    _service_state[name] = True
    return {"ok": True, "service": name, "status": "started"}

@admin_router.post("/service/{name}/stop")
def service_stop(name: str):
    if name not in _service_state:
        return {"ok": False, "error": f"unknown service '{name}'"}
    _service_state[name] = False
    return {"ok": True, "service": name, "status": "stopped"}

@admin_router.get("/service/{name}/logs")
def service_logs(name: str, lines: int = 100):
    if name not in _service_state:
        return {"ok": False, "error": f"unknown service '{name}'"}
    sample = [f"[{time.strftime('%H:%M:%S')}] {name}: log line {i+1}" for i in range(min(max(lines, 1), 500))]
    return {"ok": True, "service": name, "logs": sample}
