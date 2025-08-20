"""Payment provider abstraction."""

from abc import ABC, abstractmethod
from typing import TypedDict, Optional, Dict, Any
from fastapi import Request

class PaymentResult(TypedDict, total=False):
    """Normalized payment result."""
    status: str                 # created|authorized|captured|failed|refunded
    provider: str
    provider_payment_id: str
    amount: int
    currency: str
    fees: Optional[int]
    raw: Dict[str, Any]

class PaymentProvider(ABC):
    """Abstract payment provider interface."""
    
    name: str
    
    @abstractmethod
    async def create_checkout(self, amount: int, currency: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Create checkout session/order.
        
        Args:
            amount: Amount in cents
            currency: Currency code (EUR, USD, etc.)
            meta: Provider-specific metadata (return_url, cancel_url, etc.)
            
        Returns:
            Dict with session/order data including approval links
        """
        pass
    
    @abstractmethod
    async def capture(self, provider_payment_id: str) -> PaymentResult:
        """Capture authorized payment.
        
        Args:
            provider_payment_id: Provider's payment/order ID
            
        Returns:
            PaymentResult with capture details
        """
        pass
    
    @abstractmethod
    async def refund(self, provider_payment_id: str, amount: Optional[int] = None) -> PaymentResult:
        """Refund payment (partial or full).
        
        Args:
            provider_payment_id: Provider's payment ID
            amount: Amount to refund in cents (None = full refund)
            
        Returns:
            PaymentResult with refund details
        """
        pass
    
    @abstractmethod
    async def verify_webhook(self, request: Request) -> Dict[str, Any]:
        """Verify webhook signature and return event data.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Verified webhook event data
            
        Raises:
            Exception: If signature verification fails
        """
        pass
