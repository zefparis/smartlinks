"""PayPal Checkout provider implementation."""

import os
import json
import hashlib
import hmac
import base64
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from fastapi import Request, HTTPException
import logging

from .base import PaymentProvider, PaymentResult

logger = logging.getLogger(__name__)

class PayPalProvider(PaymentProvider):
    """PayPal Checkout Orders v2 provider."""
    
    name = "paypal_checkout"
    
    def __init__(self):
        self.client_id = os.getenv("PP_CLIENT_ID")
        self.client_secret = os.getenv("PP_SECRET")
        self.webhook_id = os.getenv("PP_WEBHOOK_ID")
        self.is_live = os.getenv("PP_LIVE", "0") == "1"
        
        if not all([self.client_id, self.client_secret]):
            raise ValueError("PayPal credentials not configured")
        
        self.base_url = "https://api-m.paypal.com" if self.is_live else "https://api-m.sandbox.paypal.com"
        self._access_token = None
        self._token_expires = None
    
    async def _get_access_token(self) -> str:
        """Get OAuth access token with caching."""
        if self._access_token and self._token_expires and datetime.now() < self._token_expires:
            return self._access_token
        
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/oauth2/token",
                headers={
                    "Authorization": f"Basic {auth}",
                    "Accept": "application/json",
                    "Accept-Language": "en_US",
                },
                data="grant_type=client_credentials"
            )
            response.raise_for_status()
            
            data = response.json()
            self._access_token = data["access_token"]
            # Token expires in seconds, cache with 5min buffer
            expires_in = data.get("expires_in", 3600)
            self._token_expires = datetime.now() + timedelta(seconds=expires_in - 300)
            
            return self._access_token
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                           idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        """Make authenticated request to PayPal API."""
        token = await self._get_access_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if idempotency_key:
            headers["PayPal-Request-Id"] = idempotency_key
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method,
                f"{self.base_url}{endpoint}",
                headers=headers,
                json=data if data else None
            )
            
            if response.status_code >= 400:
                logger.error(f"PayPal API error {response.status_code}: {response.text}")
                response.raise_for_status()
            
            return response.json() if response.content else {}
    
    async def create_checkout(self, amount: int, currency: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Create PayPal order for checkout."""
        # Generate idempotency key from request data
        idempotency_data = f"{amount}:{currency}:{meta.get('reference_id', '')}"
        idempotency_key = meta.get('idempotency_key') or hashlib.sha256(idempotency_data.encode()).hexdigest()[:32]
        
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": currency.upper(),
                    "value": f"{amount / 100:.2f}"  # Convert cents to decimal
                },
                "reference_id": meta.get("reference_id", f"order_{idempotency_key[:8]}")
            }],
            "application_context": {
                "return_url": meta.get("return_url", "https://example.com/return"),
                "cancel_url": meta.get("cancel_url", "https://example.com/cancel"),
                "brand_name": meta.get("brand_name", "SmartLinks"),
                "landing_page": "BILLING",
                "user_action": "PAY_NOW"
            }
        }
        
        try:
            result = await self._make_request("POST", "/v2/checkout/orders", order_data, idempotency_key)
            
            # Extract approval link
            approval_link = None
            for link in result.get("links", []):
                if link.get("rel") == "approve":
                    approval_link = link.get("href")
                    break
            
            return {
                "id": result["id"],
                "status": result["status"],
                "approval_url": approval_link,
                "raw": result
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"PayPal create order failed: {e.response.text}")
            raise HTTPException(status_code=400, detail=f"PayPal order creation failed: {e}")
    
    async def capture(self, provider_payment_id: str) -> PaymentResult:
        """Capture PayPal order."""
        try:
            result = await self._make_request("POST", f"/v2/checkout/orders/{provider_payment_id}/capture")
            
            # Extract capture details
            capture_data = None
            purchase_units = result.get("purchase_units", [])
            if purchase_units:
                captures = purchase_units[0].get("payments", {}).get("captures", [])
                if captures:
                    capture_data = captures[0]
            
            if not capture_data:
                raise ValueError("No capture data found in response")
            
            amount_cents = int(float(capture_data["amount"]["value"]) * 100)
            
            # Extract fees if available
            fees = None
            seller_receivable_breakdown = capture_data.get("seller_receivable_breakdown")
            if seller_receivable_breakdown:
                paypal_fee = seller_receivable_breakdown.get("paypal_fee")
                if paypal_fee:
                    fees = int(float(paypal_fee["value"]) * 100)
            
            return PaymentResult(
                status="captured",
                provider=self.name,
                provider_payment_id=capture_data["id"],  # Use capture ID, not order ID
                amount=amount_cents,
                currency=capture_data["amount"]["currency_code"],
                fees=fees,
                raw=result
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"PayPal capture failed: {e.response.text}")
            error_detail = "Payment capture failed"
            try:
                error_data = e.response.json()
                if "details" in error_data:
                    error_detail = error_data["details"][0].get("description", error_detail)
            except:
                pass
            
            return PaymentResult(
                status="failed",
                provider=self.name,
                provider_payment_id=provider_payment_id,
                amount=0,
                currency="EUR",
                raw={"error": error_detail}
            )
    
    async def refund(self, provider_payment_id: str, amount: Optional[int] = None) -> PaymentResult:
        """Refund PayPal capture."""
        refund_data = {}
        if amount is not None:
            # Partial refund - need currency from original capture
            # In real implementation, we'd fetch the original capture details
            refund_data = {
                "amount": {
                    "value": f"{amount / 100:.2f}",
                    "currency_code": "EUR"  # Should be fetched from original
                }
            }
        
        try:
            result = await self._make_request(
                "POST", 
                f"/v2/payments/captures/{provider_payment_id}/refund",
                refund_data
            )
            
            refund_amount = int(float(result["amount"]["value"]) * 100)
            
            return PaymentResult(
                status="refunded",
                provider=self.name,
                provider_payment_id=result["id"],
                amount=refund_amount,
                currency=result["amount"]["currency_code"],
                raw=result
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"PayPal refund failed: {e.response.text}")
            return PaymentResult(
                status="failed",
                provider=self.name,
                provider_payment_id=provider_payment_id,
                amount=0,
                currency="EUR",
                raw={"error": "Refund failed"}
            )
    
    async def verify_webhook(self, request: Request) -> Dict[str, Any]:
        """Verify PayPal webhook signature."""
        if not self.webhook_id:
            raise ValueError("PayPal webhook ID not configured")
        
        body = await request.body()
        headers = dict(request.headers)
        
        # PayPal webhook verification
        verification_data = {
            "auth_algo": headers.get("paypal-auth-algo"),
            "cert_id": headers.get("paypal-cert-id"),
            "transmission_id": headers.get("paypal-transmission-id"),
            "transmission_sig": headers.get("paypal-transmission-sig"),
            "transmission_time": headers.get("paypal-transmission-time"),
            "webhook_id": self.webhook_id,
            "webhook_event": json.loads(body.decode())
        }
        
        try:
            result = await self._make_request(
                "POST",
                "/v1/notifications/verify-webhook-signature",
                verification_data
            )
            
            if result.get("verification_status") != "SUCCESS":
                raise HTTPException(status_code=400, detail="Invalid webhook signature")
            
            return json.loads(body.decode())
            
        except httpx.HTTPStatusError as e:
            logger.error(f"PayPal webhook verification failed: {e.response.text}")
            raise HTTPException(status_code=400, detail="Webhook verification failed")
