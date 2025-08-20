"""
Clicks Router - Handles click-related endpoints for the SmartLinks Autopilot.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import random
import logging

from ..db import SessionLocal
from ..models import Click

# Set up logging
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clicks", tags=["clicks"])

# Helper function to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Sample data for demo purposes
COUNTRIES = ["FR", "US", "DE", "GB", "JP", "CA", "AU", "BR", "IN", "SG"]
DEVICES = ["mobile", "desktop", "tablet"]

@router.get("/recent", response_model=List[dict])
async def get_recent_clicks(
    limit: int = Query(50, ge=1, le=1000, description="Number of recent clicks to return (1-1000)"),
    days: Optional[int] = Query(None, ge=1, le=365, description="Filter by last N days"),
    device: Optional[str] = Query(None, description="Filter by device type (mobile, desktop, tablet)"),
    country: Optional[str] = Query(None, description="Filter by country code (e.g., FR, US)"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO 8601 format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO 8601 format)"),
    db: Session = Depends(get_db)
):
    """
    Get recent clicks with optional filtering and pagination.
    
    Args:
        limit: Maximum number of clicks to return (1-1000)
        days: Optional filter for last N days (ignored if start_date/end_date provided)
        device: Optional filter by device type
        country: Optional filter by country code (2-letter ISO code)
        start_date: Optional start date for filtering (ISO 8601 format)
        end_date: Optional end date for filtering (ISO 8601 format)
        
    Returns:
        List of recent click objects with id, timestamp, country, and device
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        # Handle time range
        now = datetime.now(timezone.utc)
        
        # Use explicit date range if provided, otherwise use days parameter
        if start_date or end_date:
            if not start_date:
                start_date = now - timedelta(days=30)  # Default to last 30 days if no start_date
            if not end_date:
                end_date = now
                
            # Ensure timezone awareness
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
        elif days:
            # Fall back to days parameter if no explicit date range
            end_date = now
            start_date = end_date - timedelta(days=days)
        else:
            # Default to last 24 hours if no time range specified
            end_date = now
            start_date = end_date - timedelta(days=1)
        
        # Build base query
        query = db.query(Click).order_by(Click.ts.desc())
        
        # Apply time filter
        query = query.filter(Click.ts.between(start_date, end_date))
            
        # Apply additional filters
        if device:
            query = query.filter(Click.device == device.lower())
            
        if country:
            query = query.filter(Click.geo == country.upper())
        
        # Execute query with limit
        clicks = query.limit(limit).all()
        
        # Format response
        if not clicks:
            logger.info("No clicks found in database, returning empty list")
            return []
            
        # Process results
        results = []
        for click in clicks:
            try:
                results.append({
                    "id": click.click_id if hasattr(click, 'click_id') else f"db_{getattr(click, 'id', 'unknown')}",
                    "timestamp": click.ts.isoformat() if click.ts else None,
                    "country": click.geo or "Unknown",
                    "device": (click.device or "unknown").lower(),
                    "ip": getattr(click, 'ip', None),
                    "user_agent": getattr(click, 'user_agent', None),
                    "referrer": getattr(click, 'referrer', None),
                    "segment_id": getattr(click, 'segment_id', None)
                })
            except Exception as e:
                logger.warning(f"Error formatting click {getattr(click, 'id', 'unknown')}: {e}")
                continue
                
        return results
            
    except ValueError as ve:
        logger.error(f"Invalid parameter value: {ve}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid parameter value: {str(ve)}"
        )
    except Exception as e:
        logger.error(f"Error in get_recent_clicks: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving recent clicks: {str(e)}"
        )
