"""Payment providers module."""

from .base import PaymentProvider, PaymentResult
from .stripe_provider import StripeProvider
from .paypal_provider import PayPalProvider

# Provider registry
_PROVIDERS = {
    "stripe_cards": StripeProvider,
    "paypal_checkout": PayPalProvider,
}

def resolve_provider(name: str) -> PaymentProvider:
    """Resolve provider by name."""
    if name not in _PROVIDERS:
        raise ValueError(f"Unknown provider: {name}")
    return _PROVIDERS[name]()

__all__ = ["PaymentProvider", "PaymentResult", "resolve_provider"]
