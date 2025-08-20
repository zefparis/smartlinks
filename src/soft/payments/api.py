"""Unified payments API endpoints."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

from ..db import SessionLocal
from .providers import resolve_provider
from .ledger import LedgerService
from .idempotency import guard

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_role(x_role: str = Header(None)):
    """Check user role for RBAC."""
    if not x_role or x_role not in ["viewer", "operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Invalid or missing role")
    return x_role

# Request/Response models
class CreatePaymentRequest(BaseModel):
    amount: int  # Amount in cents
    currency: str  # Currency code
    provider: str  # Provider name
    meta: Dict[str, Any] = {}  # Provider-specific metadata

class CapturePaymentRequest(BaseModel):
    pass  # No additional data needed

class RefundPaymentRequest(BaseModel):
    amount: Optional[int] = None  # Partial refund amount, None = full refund
    reason: Optional[str] = None  # Refund reason for audit

@router.post("/create")
@guard("payments:create")
async def create_payment(
    request: CreatePaymentRequest,
    db: Session = Depends(get_db)
):
    """Create payment checkout session."""
    try:
        # Validate provider
        provider = resolve_provider(request.provider)
        
        # Create checkout session
        session_data = await provider.create_checkout(
            request.amount,
            request.currency,
            request.meta
        )
        
        # Record in ledger
        ledger = LedgerService(db)
        payment_id = await ledger.record_payment_created(
            provider.name,
            session_data,
            request.amount,
            request.currency,
            request.meta
        )
        
        return {
            "payment_id": payment_id,
            "provider": provider.name,
            "session": session_data,
            "status": "created"
        }
        
    except Exception as e:
        logger.error(f"Payment creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/capture/{provider}/{payment_id}")
@guard("payments:capture")
async def capture_payment(
    provider: str,
    payment_id: str,
    request: CapturePaymentRequest,
    db: Session = Depends(get_db),
    role: str = Depends(check_role)
):
    """Capture authorized payment."""
    if role not in ["operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # Resolve provider and capture
        prov = resolve_provider(provider)
        result = await prov.capture(payment_id)
        
        # Record in ledger
        ledger = LedgerService(db)
        await ledger.record_capture(result)
        
        return {
            "status": result["status"],
            "amount": result["amount"],
            "currency": result["currency"],
            "fees": result.get("fees"),
            "provider_payment_id": result["provider_payment_id"]
        }
        
    except Exception as e:
        logger.error(f"Payment capture failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/refund/{provider}/{payment_id}")
@guard("payments:refund")
async def refund_payment(
    provider: str,
    payment_id: str,
    request: RefundPaymentRequest,
    db: Session = Depends(get_db),
    role: str = Depends(check_role)
):
    """Refund payment (partial or full)."""
    if role not in ["admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # Resolve provider and refund
        prov = resolve_provider(provider)
        result = await prov.refund(payment_id, request.amount)
        
        # Record in ledger
        ledger = LedgerService(db)
        await ledger.record_refund(result)
        
        return {
            "status": result["status"],
            "amount": result["amount"],
            "currency": result["currency"],
            "provider_refund_id": result["provider_payment_id"],
            "reason": request.reason
        }
        
    except Exception as e:
        logger.error(f"Payment refund failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook/stripe")
async def webhook_stripe(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events."""
    try:
        provider = resolve_provider("stripe_cards")
        event_data = await provider.verify_webhook(request)
        
        # Store event for audit
        ledger = LedgerService(db)
        await ledger.store_provider_event(
            "stripe_cards",
            event_data.get("type", "unknown"),
            event_data,
            signature_valid=True,
            provider_id=event_data.get("id")
        )
        
        # Process specific event types
        event_type = event_data.get("type")
        if event_type == "checkout.session.completed":
            # Payment captured via checkout
            session = event_data["data"]["object"]
            payment_intent_id = session.get("payment_intent")
            if payment_intent_id:
                result = await provider.capture(session["id"])
                await ledger.record_capture(result)
        
        elif event_type == "payment_intent.succeeded":
            # Direct payment intent succeeded
            payment_intent = event_data["data"]["object"]
            # Handle if needed
            pass
        
        return {"status": "processed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stripe webhook processing failed: {e}", exc_info=True)
        # Store failed event
        try:
            ledger = LedgerService(db)
            await ledger.store_provider_event(
                "stripe_cards",
                "webhook_error",
                {"error": str(e), "request_headers": dict(request.headers)},
                signature_valid=False
            )
        except:
            pass
        raise HTTPException(status_code=400, detail="Webhook processing failed")

@router.post("/webhook/paypal")
async def webhook_paypal(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle PayPal webhook events."""
    try:
        provider = resolve_provider("paypal_checkout")
        event_data = await provider.verify_webhook(request)
        
        # Store event for audit
        ledger = LedgerService(db)
        await ledger.store_provider_event(
            "paypal_checkout",
            event_data.get("event_type", "unknown"),
            event_data,
            signature_valid=True,
            provider_id=event_data.get("id")
        )
        
        # Process specific event types
        event_type = event_data.get("event_type")
        if event_type == "CHECKOUT.ORDER.APPROVED":
            # Order approved, ready for capture
            pass
        
        elif event_type == "PAYMENT.CAPTURE.COMPLETED":
            # Payment captured
            resource = event_data.get("resource", {})
            if resource:
                # Create PaymentResult from webhook data
                from .providers.base import PaymentResult
                result = PaymentResult(
                    status="captured",
                    provider="paypal_checkout",
                    provider_payment_id=resource.get("id"),
                    amount=int(float(resource.get("amount", {}).get("value", "0")) * 100),
                    currency=resource.get("amount", {}).get("currency_code", "EUR"),
                    raw=event_data
                )
                await ledger.record_capture(result)
        
        elif event_type == "PAYMENT.CAPTURE.REFUNDED":
            # Payment refunded
            resource = event_data.get("resource", {})
            if resource:
                from .providers.base import PaymentResult
                result = PaymentResult(
                    status="refunded",
                    provider="paypal_checkout", 
                    provider_payment_id=resource.get("id"),
                    amount=int(float(resource.get("amount", {}).get("value", "0")) * 100),
                    currency=resource.get("amount", {}).get("currency_code", "EUR"),
                    raw=event_data
                )
                await ledger.record_refund(result)
        
        return {"status": "processed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PayPal webhook processing failed: {e}", exc_info=True)
        # Store failed event
        try:
            ledger = LedgerService(db)
            await ledger.store_provider_event(
                "paypal_checkout",
                "webhook_error",
                {"error": str(e), "request_headers": dict(request.headers)},
                signature_valid=False
            )
        except:
            pass
        raise HTTPException(status_code=400, detail="Webhook processing failed")

@router.get("/balances")
async def get_balances(
    currency: str = "EUR",
    db: Session = Depends(get_db),
    role: str = Depends(check_role)
):
    """Get current balances by currency."""
    if role not in ["viewer", "operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        ledger = LedgerService(db)
        balances = ledger.get_balances_by_currency(currency)
        
        return {
            "currency": currency,
            "balances": balances,
            "total_cash": balances.get(f"platform:cash:{currency.lower()}", 0),
            "total_receivables": balances.get(f"platform:receivables:{currency.lower()}", 0)
        }
        
    except Exception as e:
        logger.error(f"Balance retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve balances")
