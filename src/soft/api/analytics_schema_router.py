"""
Analytics Schema API Router - Provides schema information for debugging
"""
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/schema")
async def get_analytics_schema():
    """
    Endpoint pour exposer les schémas JSON attendus par le frontend
    Utile pour debug et validation des contrats API
    """
    
    schemas = {
        "devices_endpoint": {
            "url": "/api/analytics/devices",
            "method": "GET",
            "parameters": {
                "segment_id": "string (optional)",
                "start_date": "string YYYY-MM-DD (optional)",
                "end_date": "string YYYY-MM-DD (optional)"
            },
            "response_format": {
                "devices": [
                    {
                        "device": "string (mobile/desktop/tablet)",
                        "clicks": "number",
                        "conversions": "number", 
                        "conversion_rate": "number (0-1)",
                        "revenue": "number",
                        "revenue_per_click": "number"
                    }
                ],
                "total_clicks": "number",
                "total_conversions": "number",
                "overall_conversion_rate": "number"
            },
            "frontend_mapping": {
                "note": "Frontend expects 'count' field but backend returns 'clicks'",
                "mapping": "DeviceStats.count = backend.clicks"
            }
        },
        
        "countries_endpoint": {
            "url": "/api/analytics/countries",
            "method": "GET", 
            "parameters": {
                "days": "number (default 30)",
                "limit": "number (default 10)"
            },
            "response_format": {
                "countries": [
                    {
                        "country": "string (ISO code)",
                        "clicks": "number",
                        "conversions": "number",
                        "revenue": "number",
                        "conversion_rate": "number"
                    }
                ]
            },
            "frontend_mapping": {
                "note": "Frontend expects direct array but backend returns wrapped object",
                "mapping": "Frontend gets response.countries"
            }
        },
        
        "clicks_history_endpoint": {
            "url": "/api/analytics/clicks/history",
            "method": "GET",
            "parameters": {
                "days": "number (default 30)",
                "segment_id": "string (optional)",
                "device": "string (optional)",
                "country": "string (optional)"
            },
            "response_format": {
                "history": [
                    {
                        "date": "string YYYY-MM-DD",
                        "clicks": "number",
                        "conversions": "number", 
                        "revenue": "number"
                    }
                ],
                "total_clicks": "number",
                "total_conversions": "number",
                "date_range": {
                    "start": "string",
                    "end": "string"
                }
            },
            "frontend_mapping": {
                "note": "Frontend expects direct array but backend returns wrapped object",
                "mapping": "Frontend gets response.history"
            }
        },
        
        "traffic_by_segment_endpoint": {
            "url": "/api/analytics/traffic-by-segment",
            "method": "GET",
            "parameters": {
                "days": "number (default 30)",
                "limit": "number (default 20)"
            },
            "response_format": {
                "segments": [
                    {
                        "segment_id": "string",
                        "geo": "string",
                        "device": "string", 
                        "clicks": "number",
                        "conversions": "number",
                        "revenue": "number",
                        "conversion_rate": "number",
                        "revenue_per_click": "number"
                    }
                ],
                "totals": {
                    "clicks": "number",
                    "conversions": "number", 
                    "revenue": "number",
                    "conversion_rate": "number"
                }
            }
        },
        
        "health_endpoint": {
            "url": "/api/analytics/health",
            "method": "GET",
            "response_format": {
                "status": "string",
                "database": {
                    "clicks": "number",
                    "conversions": "number",
                    "segments": "number",
                    "offers": "number",
                    "creators": "number"
                },
                "recent_activity": {
                    "last_click": "object or null",
                    "last_conversion": "object or null"
                }
            }
        }
    }
    
    return {
        "version": "1.0.0",
        "generated_at": "2025-01-19T19:05:00Z",
        "description": "Schémas des endpoints analytics SmartLinks",
        "schemas": schemas,
        "common_issues": [
            "Frontend DeviceStats.count vs backend clicks field mismatch",
            "Backend returns wrapped objects {data: [...]} but frontend expects direct arrays",
            "Date formats must be YYYY-MM-DD for filters",
            "Conversion rates are decimals (0.15 = 15%)"
        ],
        "debugging_tips": [
            "Check browser console for 'DEBUG' logs from api.ts",
            "Use /api/analytics/health to verify data presence",
            "Backend logs analytics requests and responses",
            "All endpoints support CORS for localhost:3000"
        ]
    }
