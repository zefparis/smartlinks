"""
Payout Engine - Système de payout automatique live avec tests réels
Gère les virements automatiques Stripe/PayPal avec validation et monitoring
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import stripe
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import Payment, Payout, PayoutBatch, User
from .treasury import TreasuryService
from .providers.stripe_provider import StripeProvider
from .providers.paypal_provider import PayPalProvider
from ..models.notifications import NotificationService

logger = logging.getLogger(__name__)

class PayoutEngine:
    """Engine de payout automatique avec tests live et monitoring."""
    
    def __init__(self, db: Session):
        self.db = db
        self.treasury = TreasuryService(db)
        self.stripe_provider = StripeProvider()
        self.paypal_provider = PayPalProvider()
        self.notifications = NotificationService(db)
        
        # Configuration
        self.min_payout_amount = int(os.getenv("MIN_PAYOUT_AMOUNT", "1000"))  # 10€ en centimes
        self.max_payout_amount = int(os.getenv("MAX_PAYOUT_AMOUNT", "100000000"))  # 1M€ en centimes
        self.test_mode = os.getenv("PAYOUT_TEST_MODE", "false").lower() == "true"
        self.auto_execute = os.getenv("PAYOUT_AUTO_EXECUTE", "false").lower() == "true"
        
    async def process_automatic_payouts(self) -> Dict[str, Any]:
        """Traite tous les payouts automatiques éligibles."""
        logger.info("🚀 Starting automatic payout processing")
        
        results = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "total_amount": 0,
            "errors": [],
            "payouts": []
        }
        
        try:
            # 1. Identifier les utilisateurs éligibles
            eligible_users = await self._get_eligible_users()
            logger.info(f"Found {len(eligible_users)} eligible users for payout")
            
            # 2. Créer les batches de payout
            payout_batch = await self._create_payout_batch(eligible_users)
            
            # 3. Exécuter les payouts
            for payout in payout_batch.payouts:
                try:
                    result = await self._execute_single_payout(payout)
                    results["processed"] += 1
                    results["total_amount"] += payout.amount
                    results["payouts"].append({
                        "payout_id": payout.id,
                        "user_id": payout.user_id,
                        "amount": payout.amount,
                        "status": result.status,
                        "provider": payout.provider
                    })
                    
                    if result.status == "success":
                        results["succeeded"] += 1
                        await self._notify_payout_success(payout, result)
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Payout {payout.id}: {result.error}")
                        await self._notify_payout_failure(payout, result.error)
                        
                except Exception as e:
                    logger.error(f"Error processing payout {payout.id}: {e}")
                    results["failed"] += 1
                    results["errors"].append(f"Payout {payout.id}: {str(e)}")
                    await self._notify_payout_failure(payout, str(e))
            
            # 4. Finaliser le batch
            await self._finalize_batch(payout_batch, results)
            
        except Exception as e:
            logger.error(f"Critical error in automatic payout processing: {e}")
            results["errors"].append(f"Critical error: {str(e)}")
            await self._notify_critical_error(str(e))
        
        logger.info(f"✅ Payout processing completed: {results}")
        return results
    
    async def _get_eligible_users(self) -> List[Dict[str, Any]]:
        """Identifie les utilisateurs éligibles pour un payout."""
        # Requête pour trouver les utilisateurs avec balance >= seuil minimum
        query = """
        SELECT 
            u.id as user_id,
            u.email,
            u.payout_method,
            u.payout_details,
            COALESCE(SUM(p.amount), 0) - COALESCE(SUM(po.amount), 0) as balance
        FROM users u
        LEFT JOIN payments p ON p.user_id = u.id AND p.status = 'captured'
        LEFT JOIN payouts po ON po.user_id = u.id AND po.status IN ('completed', 'processing')
        WHERE u.payout_enabled = true
        AND u.payout_method IS NOT NULL
        AND u.payout_details IS NOT NULL
        GROUP BY u.id, u.email, u.payout_method, u.payout_details
        HAVING balance >= :min_amount
        """
        
        result = self.db.execute(query, {"min_amount": self.min_payout_amount})
        return [dict(row) for row in result.fetchall()]
    
    async def _create_payout_batch(self, eligible_users: List[Dict]) -> PayoutBatch:
        """Crée un batch de payouts."""
        batch = PayoutBatch(
            created_at=datetime.utcnow(),
            status="created",
            total_amount=0,
            total_count=len(eligible_users)
        )
        self.db.add(batch)
        self.db.flush()
        
        total_amount = 0
        for user_data in eligible_users:
            payout = Payout(
                batch_id=batch.id,
                user_id=user_data["user_id"],
                amount=user_data["balance"],
                currency="EUR",
                provider=self._get_provider_for_method(user_data["payout_method"]),
                method=user_data["payout_method"],
                recipient_details=user_data["payout_details"],
                status="pending",
                created_at=datetime.utcnow()
            )
            self.db.add(payout)
            total_amount += payout.amount
        
        batch.total_amount = total_amount
        self.db.commit()
        
        # Recharger avec les payouts
        self.db.refresh(batch)
        return batch
    
    async def _execute_single_payout(self, payout: Payout) -> Dict[str, Any]:
        """Exécute un payout individuel."""
        logger.info(f"🔄 Executing payout {payout.id} for user {payout.user_id}")
        
        try:
            # Validation des montants
            if payout.amount < self.min_payout_amount:
                return {"status": "failed", "error": "Amount below minimum threshold"}
            
            if payout.amount > self.max_payout_amount:
                return {"status": "failed", "error": "Amount above maximum threshold"}
            
            # Sélection du provider
            if payout.provider == "stripe":
                result = await self._execute_stripe_payout(payout)
            elif payout.provider == "paypal":
                result = await self._execute_paypal_payout(payout)
            else:
                return {"status": "failed", "error": f"Unknown provider: {payout.provider}"}
            
            # Mise à jour du statut
            payout.status = result["status"]
            payout.external_id = result.get("external_id")
            payout.executed_at = datetime.utcnow()
            payout.metadata = result.get("metadata", {})
            
            if result["status"] == "failed":
                payout.error_message = result.get("error")
            
            self.db.commit()
            return result
            
        except Exception as e:
            logger.error(f"Error executing payout {payout.id}: {e}")
            payout.status = "failed"
            payout.error_message = str(e)
            self.db.commit()
            return {"status": "failed", "error": str(e)}
    
    async def _execute_stripe_payout(self, payout: Payout) -> Dict[str, Any]:
        """Exécute un payout via Stripe."""
        try:
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
            
            # Créer le payout Stripe
            stripe_payout = stripe.Payout.create(
                amount=payout.amount,
                currency=payout.currency.lower(),
                method="instant" if not self.test_mode else "standard",
                metadata={
                    "payout_id": str(payout.id),
                    "user_id": str(payout.user_id),
                    "batch_id": str(payout.batch_id)
                }
            )
            
            return {
                "status": "processing" if stripe_payout.status == "in_transit" else "completed",
                "external_id": stripe_payout.id,
                "metadata": {
                    "stripe_status": stripe_payout.status,
                    "arrival_date": stripe_payout.arrival_date,
                    "method": stripe_payout.method
                }
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe payout error: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _execute_paypal_payout(self, payout: Payout) -> Dict[str, Any]:
        """Exécute un payout via PayPal."""
        try:
            # Configuration PayPal
            paypal_client_id = os.getenv("PAYPAL_CLIENT_ID")
            paypal_client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
            paypal_base_url = "https://api-m.sandbox.paypal.com" if self.test_mode else "https://api-m.paypal.com"
            
            # Obtenir le token d'accès
            auth_response = await self._get_paypal_access_token(paypal_client_id, paypal_client_secret, paypal_base_url)
            access_token = auth_response["access_token"]
            
            # Créer le payout PayPal
            payout_data = {
                "sender_batch_header": {
                    "sender_batch_id": f"batch_{payout.batch_id}_{payout.id}",
                    "email_subject": "Payout from SmartLinks",
                    "email_message": "You have received a payout from SmartLinks Autopilot"
                },
                "items": [{
                    "recipient_type": "EMAIL",
                    "amount": {
                        "value": str(payout.amount / 100),  # PayPal utilise des décimales
                        "currency": payout.currency
                    },
                    "receiver": payout.recipient_details["email"],
                    "note": f"SmartLinks payout #{payout.id}",
                    "sender_item_id": str(payout.id)
                }]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{paypal_base_url}/v1/payments/payouts",
                    json=payout_data,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 201:
                    result = response.json()
                    return {
                        "status": "processing",
                        "external_id": result["batch_header"]["payout_batch_id"],
                        "metadata": {
                            "paypal_batch_status": result["batch_header"]["batch_status"],
                            "time_created": result["batch_header"]["time_created"]
                        }
                    }
                else:
                    return {"status": "failed", "error": f"PayPal API error: {response.text}"}
                    
        except Exception as e:
            logger.error(f"PayPal payout error: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _get_paypal_access_token(self, client_id: str, client_secret: str, base_url: str) -> Dict[str, Any]:
        """Obtient un token d'accès PayPal."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=(client_id, client_secret),
                headers={"Accept": "application/json", "Accept-Language": "en_US"}
            )
            response.raise_for_status()
            return response.json()
    
    def _get_provider_for_method(self, method: str) -> str:
        """Détermine le provider basé sur la méthode de payout."""
        if method in ["sepa", "bank_transfer", "card"]:
            return "stripe"
        elif method in ["paypal"]:
            return "paypal"
        else:
            return "stripe"  # Défaut
    
    async def _notify_payout_success(self, payout: Payout, result: Dict[str, Any]):
        """Notifie le succès d'un payout."""
        await self.notifications.send_email(
            to=payout.user.email,
            subject="✅ Payout Successful - SmartLinks",
            template="payout_success",
            data={
                "amount": payout.amount / 100,
                "currency": payout.currency,
                "payout_id": payout.id,
                "external_id": result.get("external_id"),
                "estimated_arrival": result.get("metadata", {}).get("arrival_date")
            }
        )
    
    async def _notify_payout_failure(self, payout: Payout, error: str):
        """Notifie l'échec d'un payout."""
        await self.notifications.send_email(
            to=payout.user.email,
            subject="❌ Payout Failed - SmartLinks",
            template="payout_failure",
            data={
                "amount": payout.amount / 100,
                "currency": payout.currency,
                "payout_id": payout.id,
                "error": error
            }
        )
        
        # Alerte admin
        await self.notifications.send_admin_alert(
            type="payout_failure",
            message=f"Payout {payout.id} failed for user {payout.user_id}: {error}",
            severity="high"
        )
    
    async def _notify_critical_error(self, error: str):
        """Notifie une erreur critique."""
        await self.notifications.send_admin_alert(
            type="payout_critical_error",
            message=f"Critical error in payout processing: {error}",
            severity="critical"
        )
    
    async def _finalize_batch(self, batch: PayoutBatch, results: Dict[str, Any]):
        """Finalise un batch de payouts."""
        batch.status = "completed" if results["failed"] == 0 else "partial"
        batch.completed_at = datetime.utcnow()
        batch.results = results
        self.db.commit()
        
        logger.info(f"✅ Batch {batch.id} finalized: {results['succeeded']}/{results['processed']} successful")

# Tâche cron pour exécution automatique
async def run_automatic_payouts():
    """Tâche cron pour les payouts automatiques."""
    from ..db import get_db
    
    db = next(get_db())
    try:
        engine = PayoutEngine(db)
        results = await engine.process_automatic_payouts()
        logger.info(f"Automatic payout run completed: {results}")
        return results
    finally:
        db.close()
