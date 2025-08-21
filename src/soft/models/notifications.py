import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Minimal notification service used by security module.
    Currently logs admin alerts; can be extended to email/Slack/etc.
    """

    def __init__(self, db=None):
        self.db = db

    async def send_admin_alert(
        self,
        type: str,
        message: str,
        severity: str = "info",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        logger.warning(
            "[ADMIN ALERT] type=%s severity=%s message=%s metadata=%s",
            type,
            severity,
            message,
            metadata or {},
        )
