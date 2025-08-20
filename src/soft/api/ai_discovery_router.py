from fastapi import APIRouter, Depends, HTTPException

__all__ = ['router']

from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import json
import os
import httpx
from pydantic import BaseModel

from ..db import SessionLocal
from ..models import Click, Conversion

# Initialize router without prefix (will be added in router.py)
router = APIRouter()

# Dependency DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Models
class DiscoveryRequest(BaseModel):
    days: int = 30

class DiscoveryResponse(BaseModel):
    opportunities: List[Dict[str, str]]
    alerts: List[Dict[str, str]]
    projections: Dict[str, float]

# Helper Functions
async def get_ai_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    """Send data to OpenAI for analysis and return the response."""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    system_prompt = """
    You are the AI Director of SmartLinks. Analyze this click, conversion, and revenue data.
    
    Your tasks:
    1. Detect opportunities by country, device, or time period
    2. Identify suspicious traffic (e.g., many clicks but 0 conversions)
    3. Provide 7-day projections based on historical data
    
    Format your response as a valid JSON object with the following structure:
    {
        "opportunities": [
            {
                "segment": "Mobile users in Cameroon",
                "reason": "CTR 2x higher than desktop"
            }
        ],
        "alerts": [
            {
                "issue": "Suspicious traffic",
                "details": "High clicks from Country X but 0 conversions"
            }
        ],
        "projections": {
            "clicks_next_7_days": 12000,
            "expected_revenue": 540.5
        }
    }
    """
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{openai_base_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_api_key}"
                },
                json={
                    "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps(data, indent=2)}
                    ],
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"}
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"OpenAI API error: {response.text}"
                )
            
            result = response.json()
            return json.loads(result["choices"][0]["message"]["content"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

def get_analytics_data(db: Session, days: int) -> Dict[str, Any]:
    """Fetch analytics data from the database."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Get device stats
    device_stats = db.query(
        Click.device,
        func.count(Click.id).label("clicks"),
        func.sum(case((Conversion.id.isnot(None), 1), else_=0)).label("conversions"),
        func.coalesce(func.sum(Conversion.revenue), 0).label("revenue")
    ).outerjoin(
        Conversion, Click.click_id == Conversion.click_id
    ).filter(
        Click.timestamp >= start_date,
        Click.timestamp <= end_date
    ).group_by(
        Click.device
    ).all()
    
    # Get country stats
    country_stats = db.query(
        Click.geo.label("country"),
        func.count(Click.id).label("clicks"),
        func.sum(case((Conversion.id.isnot(None), 1), else_=0)).label("conversions"),
        func.coalesce(func.sum(Conversion.revenue), 0).label("revenue")
    ).outerjoin(
        Conversion, Click.click_id == Conversion.click_id
    ).filter(
        Click.timestamp >= start_date,
        Click.timestamp <= end_date,
        Click.geo.isnot(None)
    ).group_by(
        Click.geo
    ).all()
    
    # Get daily stats
    daily_stats = db.query(
        func.date(Click.timestamp).label("date"),
        func.count(Click.id).label("clicks"),
        func.sum(case((Conversion.id.isnot(None), 1), else_=0)).label("conversions"),
        func.coalesce(func.sum(Conversion.revenue), 0).label("revenue")
    ).outerjoin(
        Conversion, Click.click_id == Conversion.click_id
    ).filter(
        Click.timestamp >= start_date,
        Click.timestamp <= end_date
    ).group_by(
        func.date(Click.timestamp)
    ).order_by(
        func.date(Click.timestamp)
    ).all()
    
    return {
        "time_period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days
        },
        "device_stats": [dict(row._asdict()) for row in device_stats],
        "country_stats": [dict(row._asdict()) for row in country_stats],
        "daily_stats": [{
            "date": row.date.isoformat(),
            "clicks": row.clicks,
            "conversions": row.conversions,
            "revenue": float(row.revenue) if row.revenue else 0.0
        } for row in daily_stats]
    }

# API Endpoint
@router.post("/discovery", response_model=DiscoveryResponse)
async def run_discovery(
    request: DiscoveryRequest,
    db: Session = Depends(get_db)
):
    """
    Run AI-powered discovery on click data.
    
    - **days**: Number of days of data to analyze (default: 30)
    """
    try:
        # Get analytics data
        analytics_data = get_analytics_data(db, request.days)
        
        # Get AI analysis
        ai_response = await get_ai_analysis(analytics_data)
        
        return {
            "opportunities": ai_response.get("opportunities", []),
            "alerts": ai_response.get("alerts", []),
            "projections": ai_response.get("projections", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
