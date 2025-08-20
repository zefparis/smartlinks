from fastapi import APIRouter
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_router = APIRouter()

# --- Health check ---
@api_router.get("/health")
async def health():
    return {"status": "ok"}


# --- System status (levels for UI) ---
@api_router.get("/status")
async def status_endpoint() -> Dict[str, Any]:
    """Return system status levels suitable for dashboard indicators.
    Levels: active | warning | down
    """
    now = datetime.now(timezone.utc).isoformat()
    # In a real impl, compute from subsystems; here we return sane defaults
    return {
        "router": "active",
        "autopilot": "active",
        "probes": "warning",
        "ts": now,
    }


# --- Metrics (matches frontend MetricsResponse) ---
@api_router.get("/metrics")
async def metrics() -> Dict[str, Any]:
    return {
        "clicks_total": 0,
        "last_click_id": None,
        "last_click_time": None,
        "segments": [
            {"segment": "US:mobile", "count": 10, "avg_risk": 0.12},
            {"segment": "FR:desktop", "count": 5, "avg_risk": 0.08},
        ],
    }


# --- Stats (matches frontend StatsResponse) ---
@api_router.get("/stats")
async def stats() -> Dict[str, Any]:
    return {
        "clicks_total": 15,
        "fraud_suspects": 1,
        "approved": 9,
        "fraud_rate": 0.066,
        "approval_rate": 0.6,
    }


# --- Recent clicks (array, matches frontend expectation) ---
@api_router.get("/clicks/recent")
async def recent_clicks(limit: int = 10) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "id": f"clk_{i}",
            "slug": "offer-123",
            "device": "mobile" if i % 2 == 0 else "desktop",
            "geo": "US" if i % 2 == 0 else "FR",
            "created_at": now,
            "status": "approved" if i % 3 else "pending",
            "revenue": round(1.0 + i * 0.1, 2),
        }
        for i in range(limit)
    ]
