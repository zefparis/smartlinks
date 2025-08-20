"""
Payment Alerts & Monitoring - Alertes et logs complets pour incidents paiement
Système de monitoring en temps réel avec notifications email/SMS/dashboard
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json
from dataclasses import dataclass, asdict

from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Float, JSON
from sqlalchemy.ext.declarative import declarative_base

from ..models.base import Base
from ..models.notifications import NotificationService
from .models import Payment, Payout, Refund

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    PAYMENT_FAILED = "payment_failed"
    PAYOUT_FAILED = "payout_failed"
    REFUND_FAILED = "refund_failed"
    HIGH_FAILURE_RATE = "high_failure_rate"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BALANCE_LOW = "balance_low"
    PROCESSING_DELAY = "processing_delay"
    PROVIDER_ERROR = "provider_error"
    FRAUD_DETECTED = "fraud_detected"
    COMPLIANCE_ISSUE = "compliance_issue"

@dataclass
class AlertRule:
    """Règle d'alerte configurable."""
    alert_type: AlertType
    severity: AlertSeverity
    threshold: Union[int, float]
    time_window_minutes: int
    enabled: bool = True
    notification_channels: List[str] = None
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = ["email", "dashboard"]

class PaymentAlert(Base):
    """Alertes de paiement stockées en base."""
    __tablename__ = "payment_alerts"
    
    id = Column(String, primary_key=True)
    alert_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    metadata = Column(JSON, default={})
    
    # Références
    payment_id = Column(String, nullable=True)
    payout_id = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    
    # Statut
    status = Column(String, default="active")  # active, acknowledged, resolved
    acknowledged_by = Column(String, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PaymentMonitor:
    """Système de monitoring des paiements avec alertes automatiques."""
    
    def __init__(self, db: Session):
        self.db = db
        self.notifications = NotificationService(db)
        
        # Configuration des règles d'alerte
        self.alert_rules = {
            AlertType.PAYMENT_FAILED: AlertRule(
                AlertType.PAYMENT_FAILED,
                AlertSeverity.HIGH,
                threshold=1,  # 1 échec = alerte
                time_window_minutes=5,
                notification_channels=["email", "sms", "dashboard"]
            ),
            AlertType.HIGH_FAILURE_RATE: AlertRule(
                AlertType.HIGH_FAILURE_RATE,
                AlertSeverity.CRITICAL,
                threshold=0.1,  # 10% d'échecs
                time_window_minutes=60,
                notification_channels=["email", "sms", "dashboard", "slack"]
            ),
            AlertType.PAYOUT_FAILED: AlertRule(
                AlertType.PAYOUT_FAILED,
                AlertSeverity.HIGH,
                threshold=1,
                time_window_minutes=5,
                notification_channels=["email", "dashboard"]
            ),
            AlertType.BALANCE_LOW: AlertRule(
                AlertType.BALANCE_LOW,
                AlertSeverity.MEDIUM,
                threshold=1000.0,  # 10€ en centimes
                time_window_minutes=1440,  # 24h
                notification_channels=["email", "dashboard"]
            ),
            AlertType.SUSPICIOUS_ACTIVITY: AlertRule(
                AlertType.SUSPICIOUS_ACTIVITY,
                AlertSeverity.HIGH,
                threshold=5,  # 5 tentatives suspectes
                time_window_minutes=15,
                notification_channels=["email", "sms", "dashboard"]
            )
        }
        
        # Configuration notifications
        self.admin_emails = os.getenv("ADMIN_ALERT_EMAILS", "admin@smartlinks.com").split(",")
        self.sms_numbers = os.getenv("ADMIN_ALERT_SMS", "").split(",") if os.getenv("ADMIN_ALERT_SMS") else []
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        
    async def monitor_payment_events(self):
        """Surveillance continue des événements de paiement."""
        logger.info("🔍 Starting payment monitoring cycle")
        
        try:
            # Vérifier les différents types d'alertes
            await self._check_payment_failures()
            await self._check_payout_failures()
            await self._check_failure_rates()
            await self._check_balance_levels()
            await self._check_processing_delays()
            await self._check_suspicious_activity()
            await self._check_provider_errors()
            
            logger.info("✅ Payment monitoring cycle completed")
            
        except Exception as e:
            logger.error(f"Error in payment monitoring: {e}")
            await self._create_alert(
                AlertType.PROVIDER_ERROR,
                AlertSeverity.CRITICAL,
                "Payment Monitoring Error",
                f"Critical error in payment monitoring system: {str(e)}",
                {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
            )
    
    async def _check_payment_failures(self):
        """Vérifie les échecs de paiement récents."""
        rule = self.alert_rules[AlertType.PAYMENT_FAILED]
        if not rule.enabled:
            return
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=rule.time_window_minutes)
        
        failed_payments = self.db.query(Payment).filter(
            Payment.status == 'failed',
            Payment.updated_at >= cutoff_time
        ).all()
        
        for payment in failed_payments:
            # Vérifier si alerte déjà créée
            existing_alert = self.db.query(PaymentAlert).filter(
                PaymentAlert.payment_id == payment.id,
                PaymentAlert.alert_type == AlertType.PAYMENT_FAILED.value,
                PaymentAlert.status == 'active'
            ).first()
            
            if not existing_alert:
                await self._create_alert(
                    AlertType.PAYMENT_FAILED,
                    rule.severity,
                    f"Payment Failed - {payment.id[:8]}",
                    f"Payment {payment.id} failed with amount {payment.amount/100:.2f} {payment.currency}",
                    {
                        "payment_id": payment.id,
                        "amount": payment.amount,
                        "currency": payment.currency,
                        "provider": payment.provider,
                        "error": getattr(payment, 'error_message', 'Unknown error'),
                        "user_id": payment.user_id
                    },
                    payment_id=payment.id,
                    user_id=payment.user_id,
                    notification_channels=rule.notification_channels
                )
    
    async def _check_payout_failures(self):
        """Vérifie les échecs de payout récents."""
        rule = self.alert_rules[AlertType.PAYOUT_FAILED]
        if not rule.enabled:
            return
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=rule.time_window_minutes)
        
        failed_payouts = self.db.query(Payout).filter(
            Payout.status == 'failed',
            Payout.updated_at >= cutoff_time
        ).all()
        
        for payout in failed_payouts:
            existing_alert = self.db.query(PaymentAlert).filter(
                PaymentAlert.payout_id == payout.id,
                PaymentAlert.alert_type == AlertType.PAYOUT_FAILED.value,
                PaymentAlert.status == 'active'
            ).first()
            
            if not existing_alert:
                await self._create_alert(
                    AlertType.PAYOUT_FAILED,
                    rule.severity,
                    f"Payout Failed - {payout.id[:8]}",
                    f"Payout {payout.id} failed with amount {payout.amount/100:.2f} {payout.currency}",
                    {
                        "payout_id": payout.id,
                        "amount": payout.amount,
                        "currency": payout.currency,
                        "provider": payout.provider,
                        "error": getattr(payout, 'error_message', 'Unknown error'),
                        "user_id": payout.user_id
                    },
                    payout_id=payout.id,
                    user_id=payout.user_id,
                    notification_channels=rule.notification_channels
                )
    
    async def _check_failure_rates(self):
        """Vérifie les taux d'échec élevés."""
        rule = self.alert_rules[AlertType.HIGH_FAILURE_RATE]
        if not rule.enabled:
            return
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=rule.time_window_minutes)
        
        # Calculer le taux d'échec global
        total_payments = self.db.query(Payment).filter(
            Payment.created_at >= cutoff_time
        ).count()
        
        if total_payments < 10:  # Pas assez de données
            return
        
        failed_payments = self.db.query(Payment).filter(
            Payment.created_at >= cutoff_time,
            Payment.status == 'failed'
        ).count()
        
        failure_rate = failed_payments / total_payments
        
        if failure_rate >= rule.threshold:
            # Vérifier si alerte récente existe
            recent_alert = self.db.query(PaymentAlert).filter(
                PaymentAlert.alert_type == AlertType.HIGH_FAILURE_RATE.value,
                PaymentAlert.created_at >= cutoff_time,
                PaymentAlert.status == 'active'
            ).first()
            
            if not recent_alert:
                await self._create_alert(
                    AlertType.HIGH_FAILURE_RATE,
                    rule.severity,
                    f"High Failure Rate Alert - {failure_rate:.1%}",
                    f"Payment failure rate is {failure_rate:.1%} ({failed_payments}/{total_payments}) in the last {rule.time_window_minutes} minutes",
                    {
                        "failure_rate": failure_rate,
                        "failed_count": failed_payments,
                        "total_count": total_payments,
                        "time_window": rule.time_window_minutes,
                        "threshold": rule.threshold
                    },
                    notification_channels=rule.notification_channels
                )
    
    async def _check_balance_levels(self):
        """Vérifie les niveaux de balance faibles."""
        rule = self.alert_rules[AlertType.BALANCE_LOW]
        if not rule.enabled:
            return
        
        # Simuler la vérification des balances (à adapter selon votre système)
        # Ici on pourrait vérifier les balances Stripe, PayPal, etc.
        
        low_balances = [
            {"provider": "stripe", "balance": 500, "currency": "EUR"},  # 5€
            {"provider": "paypal", "balance": 300, "currency": "EUR"}   # 3€
        ]
        
        for balance_info in low_balances:
            if balance_info["balance"] <= rule.threshold:
                await self._create_alert(
                    AlertType.BALANCE_LOW,
                    rule.severity,
                    f"Low Balance Alert - {balance_info['provider'].title()}",
                    f"{balance_info['provider'].title()} balance is low: {balance_info['balance']/100:.2f} {balance_info['currency']}",
                    balance_info,
                    notification_channels=rule.notification_channels
                )
    
    async def _check_processing_delays(self):
        """Vérifie les retards de traitement."""
        # Paiements en attente depuis plus de 30 minutes
        cutoff_time = datetime.utcnow() - timedelta(minutes=30)
        
        delayed_payments = self.db.query(Payment).filter(
            Payment.status.in_(['pending', 'processing']),
            Payment.created_at <= cutoff_time
        ).all()
        
        for payment in delayed_payments:
            existing_alert = self.db.query(PaymentAlert).filter(
                PaymentAlert.payment_id == payment.id,
                PaymentAlert.alert_type == AlertType.PROCESSING_DELAY.value,
                PaymentAlert.status == 'active'
            ).first()
            
            if not existing_alert:
                delay_minutes = (datetime.utcnow() - payment.created_at).total_seconds() / 60
                
                await self._create_alert(
                    AlertType.PROCESSING_DELAY,
                    AlertSeverity.MEDIUM,
                    f"Processing Delay - {payment.id[:8]}",
                    f"Payment {payment.id} has been processing for {delay_minutes:.0f} minutes",
                    {
                        "payment_id": payment.id,
                        "delay_minutes": delay_minutes,
                        "status": payment.status,
                        "provider": payment.provider
                    },
                    payment_id=payment.id,
                    notification_channels=["email", "dashboard"]
                )
    
    async def _check_suspicious_activity(self):
        """Vérifie les activités suspectes."""
        rule = self.alert_rules[AlertType.SUSPICIOUS_ACTIVITY]
        if not rule.enabled:
            return
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=rule.time_window_minutes)
        
        # Exemple: Plusieurs tentatives de paiement échouées depuis la même IP
        suspicious_patterns = [
            # À implémenter selon vos critères de détection de fraude
        ]
        
        for pattern in suspicious_patterns:
            await self._create_alert(
                AlertType.SUSPICIOUS_ACTIVITY,
                rule.severity,
                "Suspicious Activity Detected",
                f"Suspicious payment pattern detected: {pattern}",
                {"pattern": pattern, "detection_time": datetime.utcnow().isoformat()},
                notification_channels=rule.notification_channels
            )
    
    async def _check_provider_errors(self):
        """Vérifie les erreurs des providers de paiement."""
        # Vérifier les erreurs récurrentes par provider
        cutoff_time = datetime.utcnow() - timedelta(minutes=60)
        
        provider_errors = self.db.execute("""
            SELECT provider, COUNT(*) as error_count
            FROM payments 
            WHERE status = 'failed' 
            AND updated_at >= :cutoff_time
            GROUP BY provider
            HAVING COUNT(*) >= 5
        """, {"cutoff_time": cutoff_time}).fetchall()
        
        for provider, error_count in provider_errors:
            await self._create_alert(
                AlertType.PROVIDER_ERROR,
                AlertSeverity.HIGH,
                f"Provider Error Spike - {provider.title()}",
                f"{provider.title()} has {error_count} failed payments in the last hour",
                {
                    "provider": provider,
                    "error_count": error_count,
                    "time_window": "1 hour"
                },
                notification_channels=["email", "dashboard", "slack"]
            )
    
    async def _create_alert(self, alert_type: AlertType, severity: AlertSeverity,
                          title: str, message: str, metadata: Dict[str, Any] = None,
                          payment_id: str = None, payout_id: str = None, user_id: str = None,
                          notification_channels: List[str] = None):
        """Crée une nouvelle alerte."""
        import uuid
        
        alert = PaymentAlert(
            id=str(uuid.uuid4()),
            alert_type=alert_type.value,
            severity=severity.value,
            title=title,
            message=message,
            metadata=metadata or {},
            payment_id=payment_id,
            payout_id=payout_id,
            user_id=user_id
        )
        
        self.db.add(alert)
        self.db.commit()
        
        logger.warning(f"🚨 Alert created: {title} ({severity.value})")
        
        # Envoyer les notifications
        if notification_channels:
            await self._send_alert_notifications(alert, notification_channels)
    
    async def _send_alert_notifications(self, alert: PaymentAlert, channels: List[str]):
        """Envoie les notifications d'alerte."""
        try:
            # Email
            if "email" in channels:
                await self._send_email_alert(alert)
            
            # SMS
            if "sms" in channels and self.sms_numbers:
                await self._send_sms_alert(alert)
            
            # Slack
            if "slack" in channels and self.slack_webhook:
                await self._send_slack_alert(alert)
            
            # Dashboard (déjà stocké en base)
            
        except Exception as e:
            logger.error(f"Error sending alert notifications: {e}")
    
    async def _send_email_alert(self, alert: PaymentAlert):
        """Envoie une alerte par email."""
        severity_colors = {
            "low": "#10b981",
            "medium": "#f59e0b", 
            "high": "#ef4444",
            "critical": "#dc2626"
        }
        
        for email in self.admin_emails:
            await self.notifications.send_email(
                to=email.strip(),
                subject=f"🚨 {alert.severity.upper()} Alert: {alert.title}",
                template="payment_alert",
                data={
                    "alert_title": alert.title,
                    "alert_message": alert.message,
                    "alert_severity": alert.severity,
                    "alert_type": alert.alert_type,
                    "alert_id": alert.id,
                    "created_at": alert.created_at.strftime("%d/%m/%Y %H:%M:%S"),
                    "metadata": alert.metadata,
                    "severity_color": severity_colors.get(alert.severity, "#6b7280")
                }
            )
    
    async def _send_sms_alert(self, alert: PaymentAlert):
        """Envoie une alerte par SMS."""
        # Intégration avec service SMS (Twilio, etc.)
        sms_message = f"🚨 SmartLinks Alert: {alert.title}\n{alert.message[:100]}..."
        
        # Ici vous intégreriez votre service SMS
        logger.info(f"SMS Alert would be sent: {sms_message}")
    
    async def _send_slack_alert(self, alert: PaymentAlert):
        """Envoie une alerte sur Slack."""
        import httpx
        
        severity_colors = {
            "low": "#36a64f",
            "medium": "#ff9500", 
            "high": "#ff0000",
            "critical": "#8B0000"
        }
        
        payload = {
            "attachments": [{
                "color": severity_colors.get(alert.severity, "#cccccc"),
                "title": f"🚨 {alert.severity.upper()} Alert",
                "text": alert.title,
                "fields": [
                    {"title": "Message", "value": alert.message, "short": False},
                    {"title": "Type", "value": alert.alert_type, "short": True},
                    {"title": "Time", "value": alert.created_at.strftime("%d/%m/%Y %H:%M:%S"), "short": True}
                ]
            }]
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(self.slack_webhook, json=payload)
    
    async def get_active_alerts(self, limit: int = 50) -> List[PaymentAlert]:
        """Récupère les alertes actives."""
        return self.db.query(PaymentAlert).filter(
            PaymentAlert.status == 'active'
        ).order_by(PaymentAlert.created_at.desc()).limit(limit).all()
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Marque une alerte comme acquittée."""
        alert = self.db.query(PaymentAlert).filter(PaymentAlert.id == alert_id).first()
        if alert:
            alert.status = 'acknowledged'
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Marque une alerte comme résolue."""
        alert = self.db.query(PaymentAlert).filter(PaymentAlert.id == alert_id).first()
        if alert:
            alert.status = 'resolved'
            alert.resolved_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

# Tâche cron pour monitoring automatique
async def run_payment_monitoring():
    """Tâche cron pour le monitoring des paiements."""
    from ..db import get_db
    
    db = next(get_db())
    try:
        monitor = PaymentMonitor(db)
        await monitor.monitor_payment_events()
    finally:
        db.close()

# Configuration des tâches périodiques
MONITORING_SCHEDULE = {
    "payment_monitoring": {
        "function": run_payment_monitoring,
        "interval_minutes": 5,  # Toutes les 5 minutes
        "description": "Monitor payment events and generate alerts"
    }
}
