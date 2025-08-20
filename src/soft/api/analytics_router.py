from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
from pydantic import BaseModel
import logging

from ..db import get_db
from ..models import Click, Conversion, Segment, Offer, Creator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


# --------------------
# Pydantic Schemas
# --------------------
class DeviceStats(BaseModel):
    device: str
    count: int
    conversion_rate: float


class CountryStats(BaseModel):
    country: str
    clicks: int
    conversions: int
    revenue: float


class ClickHistoryEntry(BaseModel):
    date: str  # YYYY-MM-DD
    clicks: int
    conversions: int
    revenue: float


class ConfigResponse(BaseModel):
    app_name: str = "SmartLinks Autopilot"
    version: str = "1.0.0"
    features: List[str] = ["analytics", "clicks", "conversions"]

class DeviceStatsResponse(BaseModel):
    devices: List[Dict[str, Any]]
    total_clicks: int
    total_conversions: int
    overall_conversion_rate: float

class Period(BaseModel):
    start_date: str
    end_date: str
    days: int

class ClickHistoryResponse(BaseModel):
    history: List[Dict[str, Any]]
    total_clicks: int
    total_conversions: int
    total_revenue: float
    period: Period


# Router principal pour l'analytics

# --------------------
# Analytics Endpoints
# --------------------
@router.get("/devices", response_model=Dict[str, Any])
async def get_device_stats(
    db: Session = Depends(get_db),
    segment_id: Optional[str] = Query(None, description="Filter by segment ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Récupère les statistiques par device (mobile, desktop, tablet)
    avec métriques de conversion et revenus
    TOUJOURS retourne une structure valide même si BDD vide
    """
    try:
        logger.info(f"get_device_stats called with segment_id={segment_id}, start_date={start_date}, end_date={end_date}")
        
        # Validate date parameters
        if start_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError as e:
                logger.error(f"Invalid start_date format: {start_date}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Invalid start_date format",
                        "message": "Date must be in YYYY-MM-DD format",
                        "received": start_date,
                        "traceback": str(e)
                    }
                )
        
        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError as e:
                logger.error(f"Invalid end_date format: {end_date}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Invalid end_date format",
                        "message": "Date must be in YYYY-MM-DD format",
                        "received": end_date,
                        "traceback": str(e)
                    }
                )
        
        # Base query
        query = db.query(
            Click.device,
            func.count(Click.click_id).label('clicks'),
            func.count(Conversion.id).label('conversions'),
            func.coalesce(func.sum(Conversion.revenue), 0).label('revenue')
        ).outerjoin(Conversion, Click.click_id == Conversion.click_id)
        
        # Apply filters
        if segment_id:
            query = query.filter(Click.segment_id == segment_id)
        
        if start_date:
            start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
            query = query.filter(Click.ts >= start_timestamp)
        
        if end_date:
            end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp()) + 86399
            query = query.filter(Click.ts <= end_timestamp)
        
        # Group by device and execute
        results = query.group_by(Click.device).all()
        logger.info(f"Device stats query returned {len(results)} results")
        
        # Format response - ALWAYS return valid structure
        devices = []
        total_clicks = 0
        total_conversions = 0
        total_revenue = 0.0
        
        # If no results, return default devices with 0 stats
        if not results:
            logger.info("No device data found, returning default structure")
            default_devices = ["mobile", "desktop", "tablet"]
            for device_name in default_devices:
                devices.append({
                    "device": device_name,
                    "clicks": 0,
                    "conversions": 0,
                    "conversion_rate": 0.0,
                    "revenue": 0.0,
                    "revenue_per_click": 0.0
                })
        else:
            for device, clicks, conversions, revenue in results:
                conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
                revenue_per_click = (revenue / clicks) if clicks > 0 else 0
                
                devices.append({
                    "device": device or "unknown",
                    "clicks": clicks or 0,
                    "conversions": conversions or 0,
                    "conversion_rate": round(conversion_rate, 2),
                    "revenue": round(revenue or 0, 2),
                    "revenue_per_click": round(revenue_per_click, 2)
                })
                
                total_clicks += clicks or 0
                total_conversions += conversions or 0
                total_revenue += revenue or 0
        
        overall_conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        
        response = {
            "devices": devices,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "overall_conversion_rate": round(overall_conversion_rate, 2),
            "total_revenue": round(total_revenue, 2),
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Returning device stats: {len(devices)} devices, {total_clicks} total clicks")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Erreur get_device_stats: {e}\n{error_traceback}")
        
        # Return structured error with full traceback
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error in get_device_stats",
                "message": str(e),
                "traceback": error_traceback,
                "endpoint": "/api/analytics/devices",
                "timestamp": datetime.now().isoformat(),
                "fallback_response": {
                    "devices": [],
                    "total_clicks": 0,
                    "total_conversions": 0,
                    "overall_conversion_rate": 0.0,
                    "total_revenue": 0.0
                }
            }
        )


@router.get("/countries", response_model=Dict[str, Any])
async def get_countries_analytics(
    db: Session = Depends(get_db),
    days: int = Query(30, description="Number of days of history to return"),
    limit: int = Query(10, description="Number of top countries to return")
):
    """
    Get click and conversion statistics by country.
    TOUJOURS retourne une structure valide même si BDD vide
    """
    try:
        logger.info(f"get_countries_analytics called with days={days}, limit={limit}")
        
        # Validate parameters
        if days <= 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid days parameter",
                    "message": "Days must be a positive integer",
                    "received": days
                }
            )
        
        if limit <= 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid limit parameter",
                    "message": "Limit must be a positive integer",
                    "received": limit
                }
            )
        
        # Calculate time range using timestamps
        end_timestamp = int(datetime.now().timestamp())
        start_timestamp = end_timestamp - (days * 86400)
        
        # Query for country statistics with proper timestamp filtering
        country_stats = db.query(
            Click.geo.label('country'),
            func.count(Click.click_id).label('clicks'),
            func.count(Conversion.id).label('conversions'),
            func.coalesce(func.sum(Conversion.revenue), 0).label('revenue')
        ).outerjoin(
            Conversion, and_(
                Click.click_id == Conversion.click_id,
                Conversion.status == 'approved'
            )
        ).filter(
            Click.ts >= start_timestamp,
            Click.ts <= end_timestamp
        ).group_by(
            Click.geo
        ).order_by(
            func.count(Click.click_id).desc()
        ).limit(limit).all()
        
        logger.info(f"Country stats query returned {len(country_stats)} results")
        
        # Format response - ALWAYS return valid structure
        countries = []
        
        # If no results, return empty list but valid structure
        if not country_stats:
            logger.info("No country data found, returning empty structure")
        else:
            for country, clicks, conversions, revenue in country_stats:
                countries.append({
                    "country": country or "Unknown",
                    "clicks": int(clicks or 0),
                    "conversions": int(conversions or 0),
                    "revenue": float(revenue or 0.0),
                    "conversion_rate": round((conversions / clicks * 100) if clicks and clicks > 0 else 0, 2)
                })
        
        response = {
            "countries": countries,
            "total_countries": len(countries),
            "period": {
                "days": days,
                "start_date": datetime.fromtimestamp(start_timestamp).strftime("%Y-%m-%d"),
                "end_date": datetime.fromtimestamp(end_timestamp).strftime("%Y-%m-%d")
            },
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Returning country stats: {len(countries)} countries")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Erreur get_countries_analytics: {e}\n{error_traceback}")
        
        # Return structured error with full traceback
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error in get_countries_analytics",
                "message": str(e),
                "traceback": error_traceback,
                "endpoint": "/api/analytics/countries",
                "timestamp": datetime.now().isoformat(),
                "fallback_response": {
                    "countries": [],
                    "total_countries": 0,
                    "period": {
                        "days": days,
                        "start_date": datetime.now().strftime("%Y-%m-%d"),
                        "end_date": datetime.now().strftime("%Y-%m-%d")
                    }
                }
            }
        )


# --------------------
# Clicks History
# --------------------
@router.get("/clicks/history", response_model=ClickHistoryResponse)
async def get_click_history(
    days: int = Query(30, ge=1, le=365, description="Number of days of history to return"),
    segment_id: Optional[str] = Query(None, description="Filter by segment ID"),
    device: Optional[str] = Query(None, description="Filter by device type (mobile, desktop, tablet)"),
    country: Optional[str] = Query(None, description="Filter by country code (e.g., FR, US)"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Get click history with optional filtering by segment, device, and country.
    TOUJOURS retourne une liste de jours même si 0 clics
    """
    try:
        logger.info(f"get_click_history called with days={days}, segment_id={segment_id}, device={device}, country={country}")
        
        # Validate days parameter
        if not isinstance(days, int) or days <= 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid days parameter",
                    "message": "Days must be a positive integer between 1 and 365",
                    "received": days,
                    "type": type(days).__name__
                }
            )
        
        # Handle date range - SQLite uses timestamps (integers)
        now = datetime.now()
        if start_date and end_date:
            # Convert dates to timestamps for SQLite
            start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
            end_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp())
        else:
            # Use days parameter
            end_timestamp = int(now.timestamp())
            start_timestamp = end_timestamp - (days * 86400)
        
        logger.info(f"Timestamp range: {start_timestamp} to {end_timestamp}")
        
        # Base query with proper timestamp handling for SQLite
        query = db.query(
            func.date(func.datetime(Click.ts, 'unixepoch')).label('date'),
            func.count(Click.click_id).label('clicks'),
            func.count(Conversion.id).label('conversions'),
            func.coalesce(func.sum(Conversion.revenue), 0).label('revenue')
        ).outerjoin(
            Conversion, Click.click_id == Conversion.click_id
        ).filter(
            Click.ts >= start_timestamp,
            Click.ts <= end_timestamp
        ).group_by(
            func.date(func.datetime(Click.ts, 'unixepoch'))
        ).order_by(
            func.date(func.datetime(Click.ts, 'unixepoch'))
        )

        # Apply filters
        if segment_id:
            query = query.filter(Click.segment_id == segment_id)
        if device:
            query = query.filter(Click.device == device.lower())
        if country:
            query = query.filter(Click.geo == country.upper())

        # Execute query
        results = query.all()
        logger.info(f"Click history query returned {len(results)} results")

        # ALWAYS generate complete date range even if no data
        history = []
        current_date = datetime.fromtimestamp(start_timestamp).date()
        end_date_only = datetime.fromtimestamp(end_timestamp).date()
        
        # Create dict of actual data for quick lookup
        data_by_date = {}
        for row in results:
            try:
                row_date = row.date if isinstance(row.date, str) else row.date.isoformat()
                data_by_date[row_date] = {
                    'clicks': row.clicks or 0,
                    'conversions': row.conversions or 0,
                    'revenue': float(row.revenue) if row.revenue is not None else 0.0
                }
            except Exception as e:
                logger.warning(f"Error processing row {row}: {e}")
                continue
        
        # Generate complete date range with data or zeros
        while current_date <= end_date_only:
            date_str = current_date.isoformat()
            if date_str in data_by_date:
                history.append({
                    'date': date_str,
                    **data_by_date[date_str]
                })
            else:
                # Fill missing dates with zeros
                history.append({
                    'date': date_str,
                    'clicks': 0,
                    'conversions': 0,
                    'revenue': 0.0
                })
            current_date += timedelta(days=1)

        # Calculate totals
        total_clicks = sum(h['clicks'] for h in history)
        total_conversions = sum(h['conversions'] for h in history)
        total_revenue = sum(h['revenue'] for h in history)

        response = {
            "history": history,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "total_revenue": round(total_revenue, 2),
            "period": {
                "start_date": datetime.fromtimestamp(start_timestamp).strftime("%Y-%m-%d"),
                "end_date": datetime.fromtimestamp(end_timestamp).strftime("%Y-%m-%d"),
                "days": int(len(history))
            },
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Returning click history: {len(history)} days, {total_clicks} total clicks")
        return response

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Erreur get_click_history: {e}\n{error_traceback}")
        
        # Generate fallback empty history for the requested period
        try:
            fallback_history = []
            current_date = datetime.now().date() - timedelta(days=days)
            end_date_fallback = datetime.now().date()
            
            while current_date <= end_date_fallback:
                fallback_history.append({
                    'date': current_date.isoformat(),
                    'clicks': 0,
                    'conversions': 0,
                    'revenue': 0.0
                })
                current_date += timedelta(days=1)
        except:
            fallback_history = []
        
        # Return structured error with full traceback
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error in get_click_history",
                "message": str(e),
                "traceback": error_traceback,
                "endpoint": "/api/analytics/clicks/history",
                "timestamp": datetime.now().isoformat(),
                "fallback_response": {
                    "history": fallback_history,
                    "total_clicks": 0,
                    "total_conversions": 0,
                    "total_revenue": 0.0,
                    "period": {
                        "start_date": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
                        "end_date": datetime.now().strftime("%Y-%m-%d"),
                        "days": int(days)
                    }
                }
            }
        )


# --------------------
# Config
# --------------------
@router.get("/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    """
    Get analytics configuration and available features.
    """
    return ConfigResponse()


# Health endpoint for debugging
@router.get("/health")
async def analytics_health(db: Session = Depends(get_db)):
    """
    Health check endpoint for analytics API.
    Returns database status and sample data counts.
    """
    try:
        # Check database connectivity and data
        clicks_count = db.query(Click).count()
        conversions_count = db.query(Conversion).count()
        segments_count = db.query(Segment).count()
        offers_count = db.query(Offer).count()
        creators_count = db.query(Creator).count()
        
        # Sample recent data
        recent_clicks = db.query(Click).order_by(Click.ts.desc()).limit(5).all()
        
        return {
            "status": "healthy",
            "database": {
                "clicks": clicks_count,
                "conversions": conversions_count,
                "segments": segments_count,
                "offers": offers_count,
                "creators": creators_count
            },
            "recent_activity": {
                "recent_clicks_count": len(recent_clicks),
                "latest_click_timestamp": recent_clicks[0].ts if recent_clicks else None
            },
            "endpoints": [
                "/api/analytics/health",
                "/api/analytics/devices",
                "/api/analytics/countries",
                "/api/analytics/clicks/history",
                "/api/analytics/traffic-by-segment"
            ]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Traffic by segment endpoint (missing from frontend)
@router.get("/traffic-by-segment")
async def get_traffic_by_segment(
    db: Session = Depends(get_db),
    days: int = Query(30, description="Number of days to analyze"),
    limit: int = Query(20, description="Maximum number of segments to return")
):
    """
    Get traffic statistics by segment (geo + device combination).
    This endpoint was missing and causing the frontend Traffic by Segment to show no data.
    """
    try:
        # Calculate time range using timestamps
        end_timestamp = int(datetime.now().timestamp())
        start_timestamp = end_timestamp - (days * 86400)
        
        # Query for segment statistics
        segment_stats = db.query(
            Segment.segment_id,
            Segment.geo,
            Segment.device,
            func.count(Click.click_id).label('clicks'),
            func.count(Conversion.id).label('conversions'),
            func.coalesce(func.sum(Conversion.revenue), 0).label('revenue')
        ).outerjoin(
            Click, Segment.segment_id == Click.segment_id
        ).outerjoin(
            Conversion, and_(
                Click.click_id == Conversion.click_id,
                Conversion.status == 'approved'
            )
        ).filter(
            Click.ts >= start_timestamp,
            Click.ts <= end_timestamp
        ).group_by(
            Segment.segment_id, Segment.geo, Segment.device
        ).having(
            func.count(Click.click_id) > 0
        ).order_by(
            func.count(Click.click_id).desc()
        ).limit(limit).all()
        
        # Format response
        segments = []
        total_clicks = 0
        total_conversions = 0
        total_revenue = 0
        
        for segment_id, geo, device, clicks, conversions, revenue in segment_stats:
            total_clicks += clicks
            total_conversions += conversions
            total_revenue += float(revenue or 0)
            
            segments.append({
                "segment_id": segment_id,
                "geo": geo,
                "device": device,
                "clicks": int(clicks),
                "conversions": int(conversions),
                "revenue": float(revenue or 0),
                "conversion_rate": round((conversions / clicks * 100) if clicks > 0 else 0, 2),
                "revenue_per_click": round((float(revenue or 0) / clicks) if clicks > 0 else 0, 4)
            })
        
        return {
            "segments": segments,
            "totals": {
                "clicks": total_clicks,
                "conversions": total_conversions,
                "revenue": round(total_revenue, 2),
                "conversion_rate": round((total_conversions / total_clicks * 100) if total_clicks > 0 else 0, 2)
            },
            "period": {
                "days": days,
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp
            },
            "total_segments": len(segments)
        }
        
    except Exception as e:
        logger.error(f"Error in get_traffic_by_segment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving traffic by segment statistics"
        )
