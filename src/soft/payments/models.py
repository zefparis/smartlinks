"""Payment and ledger database models."""

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db import Base

class Account(Base):
    """Chart of accounts for double-entry bookkeeping."""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)  # e.g., 'platform:cash:eur'
    currency = Column(String(3), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    entries = relationship("Entry", back_populates="account")

class Payment(Base):
    """Payment records from all providers."""
    __tablename__ = "payments"
    
    id = Column(BigInteger, primary_key=True)
    provider = Column(String, nullable=False)  # 'stripe_cards', 'paypal_checkout'
    provider_payment_id = Column(String, unique=True, nullable=True)
    amount = Column(BigInteger, nullable=False)  # Amount in cents
    currency = Column(String(3), nullable=False)
    status = Column(String, nullable=False)  # created, authorized, captured, refunded, failed, disputed
    meta = Column(JSONB, server_default='{}', nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    refunds = relationship("Refund", back_populates="payment")
    fees = relationship("Fee", back_populates="payment")

class Refund(Base):
    """Refund records."""
    __tablename__ = "refunds"
    
    id = Column(BigInteger, primary_key=True)
    payment_id = Column(BigInteger, ForeignKey("payments.id"), nullable=False)
    provider = Column(String, nullable=False)
    provider_refund_id = Column(String, nullable=True)
    amount = Column(BigInteger, nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String, nullable=False)  # pending, refunded, failed
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    payment = relationship("Payment", back_populates="refunds")

class Fee(Base):
    """Fee records associated with payments."""
    __tablename__ = "fees"
    
    id = Column(BigInteger, primary_key=True)
    payment_id = Column(BigInteger, ForeignKey("payments.id"), nullable=False)
    provider = Column(String, nullable=False)
    amount = Column(BigInteger, nullable=False)
    currency = Column(String(3), nullable=False)
    detail = Column(JSONB, server_default='{}', nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    payment = relationship("Payment", back_populates="fees")

class Entry(Base):
    """Double-entry bookkeeping entries."""
    __tablename__ = "entries"
    
    id = Column(BigInteger, primary_key=True)
    ts = Column(DateTime, server_default=func.now(), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(BigInteger, nullable=False)  # Positive = credit, Negative = debit
    ref_type = Column(String, nullable=False)  # payment, refund, payout, fee
    ref_id = Column(BigInteger, nullable=False)
    memo = Column(Text, nullable=True)
    
    # Relationships
    account = relationship("Account", back_populates="entries")

class Payout(Base):
    """Payout records and proposals."""
    __tablename__ = "payouts"
    
    id = Column(BigInteger, primary_key=True)
    provider = Column(String, nullable=False)  # stripe, paypal
    currency = Column(String(3), nullable=False)
    amount = Column(BigInteger, nullable=False)
    status = Column(String, nullable=False)  # proposed, scheduled, processing, paid, failed
    method = Column(String, nullable=False)  # sepa, withdraw
    scheduled_for = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    external_ref = Column(String, nullable=True)  # Stripe payout ID, etc.
    meta = Column(JSONB, server_default='{}', nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

class ProviderEvent(Base):
    """Raw provider webhook events for audit and reconciliation."""
    __tablename__ = "provider_events"
    
    id = Column(BigInteger, primary_key=True)
    provider = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False)
    signature_valid = Column(Boolean, server_default='false', nullable=False)
    received_at = Column(DateTime, server_default=func.now(), nullable=False)
    provider_id = Column(String, nullable=True)  # Event ID from provider
