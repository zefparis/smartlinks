from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random

router = APIRouter(prefix="/api", tags=["admin"])

# ---- Health ----
@router.get("/health")
async def health():
    return {"status": "ok", "time": datetime.utcnow()}


# ---- Stats ----
@router.get("/stats")
async def stats():
    return {
        "total_clicks": 4500,
        "unique_visitors": 1200,
        "conversion_rate": 0.12,
    }


# ---- Metrics ----
@router.get("/metrics")
async def metrics():
    return {
        "ctr": 0.23,
        "avg_time_on_site": 75,
        "bounce_rate": 0.41,
    }


# ---- Recent Clicks ----
@router.get("/clicks/recent")
async def recent_clicks(limit: int = 10):
    return [
        {"id": i, "device": "mobile" if i % 2 == 0 else "desktop", "country": "FR"}
        for i in range(limit)
    ]


# ---- Clicks History ----
@router.get("/clicks/history")
async def clicks_history(days: int = 30):
    return {
        "days": days,
        "history": [
            {"day": f"2025-08-{i:02d}", "clicks": 100 + i}
            for i in range(1, days + 1)
        ],
    }


# ---- Analytics: Clicks History ----
@router.get("/analytics/clicks/history")
async def analytics_clicks_history(days: int = Query(30, description="Nombre de jours d'historique")):
    # Générer des données fictives pour l'historique des clics
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days-1)
    
    # Générer des données pour chaque jour
    date_range = [start_date + timedelta(days=x) for x in range(days)]
    history_data = [{
        'date': date.strftime('%Y-%m-%d'),
        'clicks': random.randint(50, 200),
        'conversions': random.randint(5, 50)
    } for date in date_range]
    
    return {
        'period': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        },
        'data': history_data
    }


# ---- Analytics: Devices ----
@router.get("/analytics/devices")
async def analytics_devices():
    # Données fictives pour les appareils
    return {
        'devices': [
            {'name': 'Mobile', 'value': 1500},
            {'name': 'Desktop', 'value': 1200},
            {'name': 'Tablet', 'value': 300},
        ],
        'total': 3000
    }


# ---- Analytics: Countries ----
@router.get("/analytics/countries")
async def analytics_countries():
    # Générer des données fictives pour les 30 derniers jours
    end_date = datetime.now()
    start_date = end_date - timedelta(days=29)  # 30 jours au total
    
    # Générer des données pour chaque jour
    date_range = [start_date + timedelta(days=x) for x in range(30)]
    clicks_data = [{
        'date': date.strftime('%Y-%m-%d'),
        'count': random.randint(50, 200)
    } for date in date_range]
    
    return {
        'period': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        },
        'clicks': clicks_data
    }


# ---- Config ----
@router.get("/config")
async def get_config():
    """Récupère la configuration actuelle du système"""
    return {
        "version": "1.0.0",
        "env": "dev",
        "features": ["links", "tracking", "analytics"],
        "services": {
            "api": True,
            "worker": True,
            "scheduler": True
        },
        "settings": {
            "maintenance_mode": False,
            "max_links_per_user": 100,
            "allow_registrations": True
        }
    }

@router.put("/config")
async def update_config(config: dict):
    """Met à jour la configuration du système"""
    # Ici, vous devriez normalement sauvegarder la configuration
    return {"status": "success", "message": "Configuration mise à jour"}

@router.get("/services/status")
async def get_services_status():
    """Récupère le statut des différents services"""
    return {
        "api": True,
        "worker": True,
        "scheduler": True,
        "database": True,
        "cache": True
    }


# ---- Admin Status ----
@router.get("/admin/status")
async def admin_status():
    return {
        "uptime": "24h",
        "services": {
            "router": "running",
            "simulate": "running",
            "autopilot": "stopped",
        },
    }


# ---- Admin Seed ----
@router.post("/admin/seed")
async def admin_seed():
    return {"status": "ok", "message": "database reseeded"}
