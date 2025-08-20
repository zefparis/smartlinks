from .analytics_router import router as analytics_router
from .assistant_router import assistant_router
from .dg_router import router as dg_router
from .ai_discovery_router import router as ai_discovery_router
from .clicks_router import router as clicks_router
from .config_router import router as config_router
from .creators_router import router as creators_router

__all__ = [
    'analytics_router',
    'clicks_router',
    'assistant_router',
    'dg_router',
    'ai_discovery_router',
    'config_router',
    'creators_router'
]
