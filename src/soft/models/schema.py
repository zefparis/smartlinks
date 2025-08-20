from sqlalchemy import Column, String, Float, Integer, BigInteger, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional, List
from ..db import Base

class Offer(Base):
    """Model for offers"""
    __tablename__ = "offers"
    
    offer_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    incent_ok = Column(Integer, default=1)
    cap_day = Column(Integer, default=10000)
    geo_allow = Column(String, default='ALL')
    status = Column(String, default='on')
    
    # Relationships
    clicks = relationship("Click", back_populates="offer")
    conversions = relationship("Conversion", back_populates="offer")


class Segment(Base):
    """Model for segments"""
    __tablename__ = "segments"
    
    segment_id = Column(String, primary_key=True, index=True)
    geo = Column(String)
    device = Column(String)
    
    # Relationships
    clicks = relationship("Click", back_populates="segment")
    payout_rates = relationship("PayoutRate", back_populates="segment")


class Creator(Base):
    """Model for creators"""
    __tablename__ = "creators"
    
    creator_id = Column(String, primary_key=True, index=True)
    q = Column(Float, default=0.5)
    hard_cap_eur = Column(Float, default=50.0)
    last_seen = Column(BigInteger, nullable=True)
    
    # Relationships
    clicks = relationship("Click", back_populates="creator")


class Click(Base):
    """Model for clicks"""
    __tablename__ = "clicks"
    
    click_id = Column(String, primary_key=True, index=True)
    ts = Column(BigInteger, index=True)  # Unix timestamp
    creator_id = Column(String, ForeignKey("creators.creator_id"), nullable=True)
    slug = Column(String)
    segment_id = Column(String, ForeignKey("segments.segment_id"), nullable=True)
    geo = Column(String)
    device = Column(String)
    fp = Column(String)  # fingerprint
    valid_final = Column(Integer, default=0)
    risk = Column(Float, default=0.0)
    offer_id = Column(String, ForeignKey("offers.offer_id"), nullable=True)
    
    # Relationships
    offer = relationship("Offer", back_populates="clicks")
    segment = relationship("Segment", back_populates="clicks")
    creator = relationship("Creator", back_populates="clicks")
    conversions = relationship("Conversion", back_populates="click")


class Conversion(Base):
    """Model for conversions"""
    __tablename__ = "conversions"
    
    id = Column(String, primary_key=True, index=True)
    ts = Column(BigInteger, index=True)  # Unix timestamp
    click_id = Column(String, ForeignKey("clicks.click_id"), nullable=False)
    offer_id = Column(String, ForeignKey("offers.offer_id"), nullable=True)
    revenue = Column(Float, default=0.0)
    status = Column(String, default="pending")
    
    # Relationships
    click = relationship("Click", back_populates="conversions")
    offer = relationship("Offer", back_populates="conversions")


class PayoutRate(Base):
    """Model for payout rates"""
    __tablename__ = "payout_rates"
    
    segment_id = Column(String, ForeignKey("segments.segment_id"), primary_key=True)
    payout = Column(Float, nullable=False)
    updated_at = Column(BigInteger)  # Unix timestamp
    
    # Relationships
    segment = relationship("Segment", back_populates="payout_rates")
