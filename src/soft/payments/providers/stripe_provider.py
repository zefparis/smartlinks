"""Stripe provider implementation."""

import os
import json
import hmac
import hashlib
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
import httpx
import logging

from .base import PaymentProvider, PaymentResult

logger = logging.getLogger(__name__)

class StripeProvider(PaymentProvider):
    """Stripe Cards provider."""
    
    name = "stripe_cards"
    
    def __init__(self):
        self.secret_key = os.getenv("STRIPE_SECRET_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        if not self.secret_key:
            raise ValueError("Stripe secret key not configured")
        
        self.base_url = "https://api.stripe.com"
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Stripe API."""
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        # Convert dict to form data for Stripe
        form_data = None
        if data:
            form_data = "&".join([f"{k}={v}" for k, v in data.items()])
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method,
                f"{self.base_url}{endpoint}",
                headers=headers,
                content=form_data
            )
            
            if response.status_code >= 400:
                logger.error(f"Stripe API error {response.status_code}: {response.text}")
                response.raise_for_status()
            
            return response.json()
    
    async def create_checkout(self, amount: int, currency: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Create Stripe checkout session."""
        session_data = {
            "payment_method_types[]": "card",
            "line_items[0][price_data][currency]": currency.lower(),
            "line_items[0][price_data][product_data][name]": meta.get("product_name", "Payment"),
            "line_items[0][price_data][unit_amount]": str(amount),
            "line_items[0][quantity]": "1",
            "mode": "payment",
            "success_url": meta.get("return_url", "https://example.com/success"),
            "cancel_url": meta.get("cancel_url", "https://example.com/cancel"),
        }
        
        if meta.get("idempotency_key"):
            session_data["client_reference_id"] = meta["idempotency_key"]
        
        try:
            result = await self._make_request("POST", "/v1/checkout/sessions", session_data)
            
            return {
                "id": result["id"],
                "status": result["status"],
                "approval_url": result["url"],
                "raw": result
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Stripe session creation failed: {e.response.text}")
            raise HTTPException(status_code=400, detail=f"Stripe session creation failed: {e}")
    
    async def capture(self, provider_payment_id: str) -> PaymentResult:
        """Capture Stripe payment intent (if needed)."""
        try:
            # For checkout sessions, payment is usually auto-captured
            # This would retrieve the payment intent and capture if needed
            result = await self._make_request("GET", f"/v1/checkout/sessions/{provider_payment_id}")
            
            payment_intent_id = result.get("payment_intent")
            if not payment_intent_id:
                raise ValueError("No payment intent found")
            
            # Get payment intent details
            pi_result = await self._make_request("GET", f"/v1/payment_intents/{payment_intent_id}")
            
            amount_cents = pi_result["amount"]
            
            # Extract fees from charges
            fees = None
            charges = pi_result.get("charges", {}).get("data", [])
            if charges:
                balance_transaction_id = charges[0].get("balance_transaction")
                if balance_transaction_id:
                    bt_result = await self._make_request("GET", f"/v1/balance_transactions/{balance_transaction_id}")
                    fees = bt_result.get("fee", 0)
            
            return PaymentResult(
                status="captured" if pi_result["status"] == "succeeded" else pi_result["status"],
                provider=self.name,
                provider_payment_id=payment_intent_id,
                amount=amount_cents,
                currency=pi_result["currency"].upper(),
                fees=fees,
                raw=pi_result
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Stripe capture failed: {e.response.text}")
            return PaymentResult(
                status="failed",
                provider=self.name,
                provider_payment_id=provider_payment_id,
                amount=0,
                currency="EUR",
                raw={"error": "Capture failed"}
            )
    
    async def refund(self, provider_payment_id: str, amount: Optional[int] = None) -> PaymentResult:
        """Refund Stripe payment."""
        refund_data = {
            "payment_intent": provider_payment_id
        }
        
        if amount is not None:
            refund_data["amount"] = str(amount)
        
        try:
            result = await self._make_request("POST", "/v1/refunds", refund_data)
            
            return PaymentResult(
                status="refunded" if result["status"] == "succeeded" else result["status"],
                provider=self.name,
                provider_payment_id=result["id"],
                amount=result["amount"],
                currency=result["currency"].upper(),
                raw=result
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Stripe refund failed: {e.response.text}")
            return PaymentResult(
                status="failed",
                provider=self.name,
                provider_payment_id=provider_payment_id,
                amount=0,
                currency="EUR",
                raw={"error": "Refund failed"}
            )
    
    async def verify_webhook(self, request: Request) -> Dict[str, Any]:
        """Verify Stripe webhook signature."""
        if not self.webhook_secret:
            raise ValueError("Stripe webhook secret not configured")
        
        body = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing signature")
        
        try:
            # Parse signature
            sig_elements = {}
            for element in signature.split(","):
                key, value = element.split("=", 1)
                sig_elements[key] = value
            
            timestamp = sig_elements.get("t")
            v1_signature = sig_elements.get("v1")
            
            if not all([timestamp, v1_signature]):
                raise ValueError("Invalid signature format")
            
            # Create expected signature
            payload = f"{timestamp}.{body.decode()}"
            expected_sig = hmac.new(
                self.webhook_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(v1_signature, expected_sig):
                raise ValueError("Signature mismatch")
            
            return json.loads(body.decode())
            
        except Exception as e:
            logger.error(f"Stripe webhook verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
