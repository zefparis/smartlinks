
from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime
from sqlalchemy import text, and_, or_, func, case
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import database session
from .db import SessionLocal, Base

def connect():
    """
    Compat wrapper for old code.
    Returns a new SQLAlchemy session.
    """
    return SessionLocal()

# Import models
from .models import (
    Offer, Segment, Creator, Click, Conversion, PayoutRate
)
from datetime import datetime

def init_db():
    """Initialize the database and create tables"""
    try:
        Base.metadata.create_all(bind=SessionLocal().get_bind())
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def upsert_offer(offer_id: str, name: str, url: str, incent_ok: int = 1, 
                cap_day: int = 10000, geo_allow: str = "ALL", status: str = "on"):
    """Insert or update an offer"""
    db = next(get_db())
    try:
        offer = db.query(Offer).filter(Offer.offer_id == offer_id).first()
        if offer:
            # Update existing offer
            offer.name = name
            offer.url = url
            offer.incent_ok = incent_ok
            offer.cap_day = cap_day
            offer.geo_allow = geo_allow
            offer.status = status
        else:
            # Create new offer
            offer = Offer(
                offer_id=offer_id,
                name=name,
                url=url,
                incent_ok=incent_ok,
                cap_day=cap_day,
                geo_allow=geo_allow,
                status=status
            )
            db.add(offer)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error in upsert_offer: {e}")
        raise
    finally:
        db.close()

def upsert_segment(seg_id: str, geo: str, device: str):
    """Insert or update a segment"""
    db = next(get_db())
    try:
        segment = db.query(Segment).filter(Segment.segment_id == seg_id).first()
        if segment:
            # Update existing segment
            segment.geo = geo
            segment.device = device
        else:
            # Create new segment
            segment = Segment(segment_id=seg_id, geo=geo, device=device)
            db.add(segment)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error in upsert_segment: {e}")
        raise
    finally:
        db.close()

def record_click(click_id: str, ts: int, creator_id: str, slug: str, seg_id: str, 
                geo: str, device: str, fp: str, offer_id: Optional[str], 
                risk: float, valid_final: int, check_creator: bool = True):
    """Record a click
    
    Args:
        click_id: Unique identifier for the click
        ts: Timestamp of the click
        creator_id: ID of the creator
        slug: Slug for the click
        seg_id: Segment ID
        geo: Geographic location
        device: Device type
        fp: Fingerprint
        offer_id: Optional offer ID
        risk: Risk score
        valid_final: Whether the click is valid
        check_creator: Whether to check if creator exists
        
    Raises:
        ValueError: If creator does not exist and check_creator is True
    """
    db = next(get_db())
    try:
        # Check if creator exists
        if check_creator and creator_id:
            creator = db.query(Creator).filter(Creator.creator_id == creator_id).first()
            if not creator:
                raise ValueError(f"Creator with id {creator_id} does not exist")
        
        # Check if click already exists
        existing = db.query(Click).filter(Click.click_id == click_id).first()
        if existing:
            # Update existing click
            existing.ts = ts
            existing.creator_id = creator_id
            existing.slug = slug
            existing.segment_id = seg_id
            existing.geo = geo
            existing.device = device
            existing.fp = fp
            existing.valid_final = valid_final
            existing.risk = risk
            existing.offer_id = offer_id
        else:
            # Create new click
            click = Click(
                click_id=click_id,
                ts=ts,
                creator_id=creator_id,
                slug=slug,
                segment_id=seg_id,
                geo=geo,
                device=device,
                fp=fp,
                valid_final=valid_final,
                risk=risk,
                offer_id=offer_id
            )
            db.add(click)
        db.commit()
    except ValueError as ve:
        db.rollback()
        logger.error(f"Validation error in record_click: {ve}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in record_click: {e}")
        raise
    finally:
        db.close()

def record_conversion(ts: int, click_id: str, offer_id: str, revenue: float, status: str):
    """Record a conversion"""
    db = next(get_db())
    try:
        conversion = Conversion(
            ts=ts,
            click_id=click_id,
            offer_id=offer_id,
            revenue=revenue,
            status=status
        )
        db.add(conversion)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error in record_conversion: {e}")
        raise
    finally:
        db.close()

def upsert_creator(creator_id: str, q: float = 0.5, hard_cap_eur: float = 50.0):
    """Insert or update a creator"""
    db = next(get_db())
    try:
        creator = db.query(Creator).filter(Creator.creator_id == creator_id).first()
        if creator:
            # Update existing creator
            creator.q = q
            creator.hard_cap_eur = hard_cap_eur
            creator.last_seen = int(datetime.now().timestamp())
        else:
            # Create new creator
            creator = Creator(
                creator_id=creator_id,
                q=q,
                hard_cap_eur=hard_cap_eur,
                last_seen=int(datetime.now().timestamp())
            )
            db.add(creator)
        db.commit()
        return creator
    except Exception as e:
        db.rollback()
        logger.error(f"Error in upsert_creator: {e}")
        raise
    finally:
        db.close()

def get_offers_for_segment(seg_id: str) -> List[Tuple[str, str]]:
    """Get all active offers for a segment"""
    db = next(get_db())
    try:
        offers = db.query(Offer.offer_id, Offer.url).filter(
            Offer.status == 'on',
            Offer.incent_ok == 1
        ).all()
        return [(offer.offer_id, offer.url) for offer in offers]
    except Exception as e:
        logger.error(f"Error in get_offers_for_segment: {e}")
        return []
    finally:
        db.close()

def set_payout_rate(seg_id: str, payout: float, ts: int, db: Session = None):
    """Set the payout rate for a segment
    
    Args:
        seg_id: The segment ID to set the payout rate for
        payout: The payout amount to set
        ts: Timestamp for the update
        db: Optional SQLAlchemy session. If not provided, a new one will be created and closed.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True
        
    try:
        # Check if payout rate exists
        payout_rate = db.query(PayoutRate).filter(PayoutRate.segment_id == seg_id).first()
        if payout_rate:
            # Update existing
            payout_rate.payout = payout
            payout_rate.updated_at = ts
        else:
            # Create new
            payout_rate = PayoutRate(
                segment_id=seg_id,
                payout=payout,
                updated_at=ts
            )
            db.add(payout_rate)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error in set_payout_rate: {e}")
        raise
    finally:
        if should_close and db:
            db.close()
        db.close()

def get_payout_rate(seg_id: str, db: Session = None) -> float:
    """Get the payout rate for a segment
    
    Args:
        seg_id: The segment ID to get the payout rate for
        db: Optional SQLAlchemy session. If not provided, a new one will be created and closed.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True
        
    try:
        payout_rate = db.query(PayoutRate).filter(PayoutRate.segment_id == seg_id).first()
        return float(payout_rate.payout) if payout_rate else 0.05
    except Exception as e:
        logger.error(f"Error in get_payout_rate: {e}")
        return 0.05
    finally:
        if should_close and db:
            db.close()

def epc_for_segment(seg_id: str, horizon_hours: int = 72, db: Session = None) -> float:
    """Calculate EPC (Earnings Per Click) for a segment
    
    Args:
        seg_id: The segment ID to calculate EPC for
        horizon_hours: Time window in hours to look back for data
        db: Optional SQLAlchemy session. If not provided, a new one will be created and closed.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True
        
    try:
        since = int(datetime.now().timestamp()) - (horizon_hours * 3600)
        
        # Get total approved revenue for the segment
        revenue_query = db.query(
            func.coalesce(func.sum(Conversion.revenue), 0.0).label('total_revenue')
        ).join(
            Click, Click.click_id == Conversion.click_id
        ).filter(
            Click.segment_id == seg_id,
            Click.ts >= since,
            Conversion.status == 'approved'
        ).scalar() or 0.0
        
        # Get total valid clicks for the segment
        valid_clicks = db.query(Click).filter(
            Click.segment_id == seg_id,
            Click.ts >= since,
            Click.valid_final == 1
        ).count()
        
        # Calculate EPC
        return revenue_query / valid_clicks if valid_clicks > 0 else 0.0
        
    except Exception as e:
        logger.error(f"Error in epc_for_segment: {e}")
        return 0.0
    finally:
        if should_close and db:
            db.close()
        db.close()
