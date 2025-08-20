"""Tests for payment providers."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx
from fastapi import Request

from ..providers.paypal_provider import PayPalProvider
from ..providers.stripe_provider import StripeProvider
from ..providers.base import PaymentResult

class TestPayPalProvider:
    """Test PayPal provider."""
    
    @pytest.fixture
    def provider(self):
        with patch.dict('os.environ', {
            'PP_CLIENT_ID': 'test_client_id',
            'PP_SECRET': 'test_secret',
            'PP_WEBHOOK_ID': 'test_webhook_id',
            'PP_LIVE': '0'
        }):
            return PayPalProvider()
    
    @pytest.mark.asyncio
    async def test_create_checkout(self, provider):
        """Test PayPal checkout creation."""
        mock_response = {
            "id": "ORDER123",
            "status": "CREATED",
            "links": [
                {"rel": "approve", "href": "https://paypal.com/approve/ORDER123"}
            ]
        }
        
        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await provider.create_checkout(
                amount=10000,  # 100 EUR
                currency="EUR",
                meta={
                    "return_url": "https://example.com/return",
                    "cancel_url": "https://example.com/cancel"
                }
            )
            
            assert result["id"] == "ORDER123"
            assert result["status"] == "CREATED"
            assert "approval_url" in result
            
            # Verify API call
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/v2/checkout/orders"
    
    @pytest.mark.asyncio
    async def test_capture(self, provider):
        """Test PayPal order capture."""
        mock_response = {
            "id": "ORDER123",
            "status": "COMPLETED",
            "purchase_units": [{
                "payments": {
                    "captures": [{
                        "id": "CAPTURE123",
                        "amount": {"value": "100.00", "currency_code": "EUR"},
                        "seller_receivable_breakdown": {
                            "paypal_fee": {"value": "3.20", "currency_code": "EUR"}
                        }
                    }]
                }
            }]
        }
        
        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await provider.capture("ORDER123")
            
            assert result["status"] == "captured"
            assert result["provider_payment_id"] == "CAPTURE123"
            assert result["amount"] == 10000  # 100 EUR in cents
            assert result["currency"] == "EUR"
            assert result["fees"] == 320  # 3.20 EUR in cents
    
    @pytest.mark.asyncio
    async def test_refund(self, provider):
        """Test PayPal refund."""
        mock_response = {
            "id": "REFUND123",
            "amount": {"value": "50.00", "currency_code": "EUR"},
            "status": "COMPLETED"
        }
        
        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await provider.refund("CAPTURE123", amount=5000)
            
            assert result["status"] == "refunded"
            assert result["provider_payment_id"] == "REFUND123"
            assert result["amount"] == 5000
            assert result["currency"] == "EUR"
    
    @pytest.mark.asyncio
    async def test_verify_webhook(self, provider):
        """Test PayPal webhook verification."""
        webhook_data = {
            "id": "EVENT123",
            "event_type": "PAYMENT.CAPTURE.COMPLETED",
            "resource": {"id": "CAPTURE123"}
        }
        
        mock_request = Mock()
        mock_request.body = AsyncMock(return_value=b'{"id":"EVENT123"}')
        mock_request.headers = {
            "paypal-auth-algo": "SHA256withRSA",
            "paypal-cert-id": "cert123",
            "paypal-transmission-id": "trans123",
            "paypal-transmission-sig": "sig123",
            "paypal-transmission-time": "2023-01-01T00:00:00Z"
        }
        
        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = {"verification_status": "SUCCESS"}
            
            result = await provider.verify_webhook(mock_request)
            
            assert result["id"] == "EVENT123"

class TestStripeProvider:
    """Test Stripe provider."""
    
    @pytest.fixture
    def provider(self):
        with patch.dict('os.environ', {
            'STRIPE_SECRET_KEY': 'sk_test_123',
            'STRIPE_WEBHOOK_SECRET': 'whsec_test'
        }):
            return StripeProvider()
    
    @pytest.mark.asyncio
    async def test_create_checkout(self, provider):
        """Test Stripe checkout session creation."""
        mock_response = {
            "id": "cs_test_123",
            "status": "open",
            "url": "https://checkout.stripe.com/pay/cs_test_123"
        }
        
        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await provider.create_checkout(
                amount=10000,
                currency="EUR",
                meta={
                    "return_url": "https://example.com/success",
                    "cancel_url": "https://example.com/cancel"
                }
            )
            
            assert result["id"] == "cs_test_123"
            assert result["status"] == "open"
            assert result["approval_url"] == "https://checkout.stripe.com/pay/cs_test_123"
    
    @pytest.mark.asyncio
    async def test_capture(self, provider):
        """Test Stripe payment capture."""
        session_response = {
            "id": "cs_test_123",
            "payment_intent": "pi_test_123"
        }
        
        pi_response = {
            "id": "pi_test_123",
            "status": "succeeded",
            "amount": 10000,
            "currency": "eur",
            "charges": {
                "data": [{
                    "balance_transaction": "txn_test_123"
                }]
            }
        }
        
        bt_response = {
            "id": "txn_test_123",
            "fee": 320
        }
        
        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [session_response, pi_response, bt_response]
            
            result = await provider.capture("cs_test_123")
            
            assert result["status"] == "captured"
            assert result["provider_payment_id"] == "pi_test_123"
            assert result["amount"] == 10000
            assert result["currency"] == "EUR"
            assert result["fees"] == 320
    
    @pytest.mark.asyncio
    async def test_verify_webhook(self, provider):
        """Test Stripe webhook verification."""
        webhook_body = b'{"id":"evt_test_123","type":"checkout.session.completed"}'
        
        mock_request = Mock()
        mock_request.body = AsyncMock(return_value=webhook_body)
        mock_request.headers = {
            "stripe-signature": "t=1234567890,v1=valid_signature"
        }
        
        with patch('hmac.compare_digest', return_value=True):
            result = await provider.verify_webhook(mock_request)
            
            assert result["id"] == "evt_test_123"
            assert result["type"] == "checkout.session.completed"

@pytest.mark.asyncio
async def test_provider_resolver():
    """Test provider resolution."""
    from ..providers import resolve_provider
    
    with patch.dict('os.environ', {
        'PP_CLIENT_ID': 'test', 'PP_SECRET': 'test',
        'STRIPE_SECRET_KEY': 'test'
    }):
        stripe_provider = resolve_provider("stripe_cards")
        assert isinstance(stripe_provider, StripeProvider)
        
        paypal_provider = resolve_provider("paypal_checkout")
        assert isinstance(paypal_provider, PayPalProvider)
        
        with pytest.raises(ValueError):
            resolve_provider("unknown_provider")
