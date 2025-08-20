"""Treasury and payout engine."""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import pytz
import logging

from .models import Payout, Account, Entry
from .ledger import LedgerService

logger = logging.getLogger(__name__)

class TreasuryService:
    """Treasury management and payout engine."""
    
    def __init__(self, db: Session):
        self.db = db
        self.ledger = LedgerService(db)
        self.timezone = pytz.timezone(os.getenv("TZ", "Europe/Paris"))
        
        # Treasury configuration
        self.payout_policy = os.getenv("TREASURY_PAYOUT_POLICY", "weekly")
        self.threshold_eur = int(os.getenv("TREASURY_THRESHOLD_EUR", "50000"))  # 500€ in cents
        self.company_iban = os.getenv("COMPANY_IBAN", "")
        self.company_bic = os.getenv("COMPANY_BIC", "")
    
    def get_cash_balances(self) -> Dict[str, Dict[str, int]]:
        """Get current cash balances by provider and currency."""
        balances = {}
        
        # Get all cash accounts
        cash_accounts = self.db.query(Account).filter(
            Account.code.like("%:cash:%")
        ).all()
        
        for account in cash_accounts:
            # Parse account code: platform:cash:eur or provider:cash:eur
            parts = account.code.split(":")
            if len(parts) >= 3:
                provider = parts[0]
                currency = parts[2].upper()
                
                balance = self.ledger.get_balance(account.code)
                
                if provider not in balances:
                    balances[provider] = {}
                balances[provider][currency] = balance
        
        return balances
    
    def should_create_payout(self, provider: str, currency: str, balance: int) -> bool:
        """Determine if a payout should be created based on policy."""
        if balance <= 0:
            return False
        
        if self.payout_policy == "manual":
            return False
        
        elif self.payout_policy == "threshold":
            if currency == "EUR" and balance >= self.threshold_eur:
                return True
            # Add other currency thresholds as needed
            return False
        
        elif self.payout_policy == "weekly":
            # Check if it's Monday and we haven't created a payout this week
            now = datetime.now(self.timezone)
            if now.weekday() == 0 and now.hour >= 9:  # Monday 9 AM
                # Check if we already have a payout this week
                week_start = now - timedelta(days=now.weekday())
                existing_payout = self.db.query(Payout).filter(
                    Payout.provider == provider,
                    Payout.currency == currency,
                    Payout.created_at >= week_start
                ).first()
                
                return existing_payout is None
        
        return False
    
    async def create_payout_proposal(self, provider: str, currency: str, amount: int) -> int:
        """Create a payout proposal."""
        # Determine payout method based on provider
        method = "sepa" if provider == "stripe" else "withdraw"
        
        payout = Payout(
            provider=provider,
            currency=currency,
            amount=amount,
            status="proposed",
            method=method,
            meta={
                "policy": self.payout_policy,
                "company_iban": self.company_iban,
                "company_bic": self.company_bic,
                "created_by": "treasury_engine"
            }
        )
        
        self.db.add(payout)
        self.db.flush()
        self.db.commit()
        
        logger.info(f"Created payout proposal: {payout.id} for {provider} {amount/100:.2f} {currency}")
        return payout.id
    
    async def execute_payout(self, payout_id: int, dry_run: bool = False) -> Dict[str, Any]:
        """Execute a payout proposal."""
        payout = self.db.query(Payout).filter(Payout.id == payout_id).first()
        if not payout:
            raise ValueError(f"Payout {payout_id} not found")
        
        if payout.status != "proposed":
            raise ValueError(f"Payout {payout_id} is not in proposed status")
        
        result = {
            "payout_id": payout_id,
            "provider": payout.provider,
            "amount": payout.amount,
            "currency": payout.currency,
            "method": payout.method,
            "dry_run": dry_run
        }
        
        if dry_run:
            result["status"] = "dry_run_success"
            return result
        
        try:
            if payout.method == "sepa" and payout.provider == "stripe":
                # Execute Stripe payout
                external_ref = await self._execute_stripe_payout(payout)
                payout.external_ref = external_ref
                payout.status = "processing"
            
            elif payout.method == "withdraw":
                # Mark as scheduled for manual withdrawal
                payout.status = "scheduled"
                payout.scheduled_for = datetime.now(self.timezone) + timedelta(days=1)
            
            payout.executed_at = datetime.now(self.timezone)
            
            # Record ledger entries
            await self.ledger.record_payout(
                payout.provider,
                payout.currency,
                payout.amount,
                payout.method,
                payout.external_ref
            )
            
            self.db.commit()
            
            result["status"] = payout.status
            result["external_ref"] = payout.external_ref
            
        except Exception as e:
            logger.error(f"Payout execution failed: {e}", exc_info=True)
            payout.status = "failed"
            payout.meta["error"] = str(e)
            self.db.commit()
            
            result["status"] = "failed"
            result["error"] = str(e)
        
        return result
    
    async def _execute_stripe_payout(self, payout: Payout) -> str:
        """Execute Stripe payout via API."""
        import httpx
        
        stripe_secret = os.getenv("STRIPE_SECRET_KEY")
        if not stripe_secret:
            raise ValueError("Stripe secret key not configured")
        
        # Convert amount to Stripe format (cents to dollars for API)
        amount_for_api = payout.amount  # Stripe API expects cents
        
        payout_data = {
            "amount": str(amount_for_api),
            "currency": payout.currency.lower(),
            "method": "instant",  # or "standard"
            "description": f"SmartLinks payout {payout.id}"
        }
        
        headers = {
            "Authorization": f"Bearer {stripe_secret}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        form_data = "&".join([f"{k}={v}" for k, v in payout_data.items()])
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.stripe.com/v1/payouts",
                headers=headers,
                content=form_data
            )
            
            if response.status_code >= 400:
                error_data = response.json()
                raise Exception(f"Stripe payout failed: {error_data}")
            
            result = response.json()
            return result["id"]
    
    async def run_payout_scheduler(self, dry_run: bool = False) -> List[Dict[str, Any]]:
        """Run the payout scheduler based on configured policy."""
        results = []
        
        try:
            balances = self.get_cash_balances()
            
            for provider, currencies in balances.items():
                for currency, balance in currencies.items():
                    if self.should_create_payout(provider, currency, balance):
                        if dry_run:
                            results.append({
                                "action": "would_create_payout",
                                "provider": provider,
                                "currency": currency,
                                "amount": balance,
                                "policy": self.payout_policy
                            })
                        else:
                            payout_id = await self.create_payout_proposal(provider, currency, balance)
                            results.append({
                                "action": "created_payout_proposal",
                                "payout_id": payout_id,
                                "provider": provider,
                                "currency": currency,
                                "amount": balance
                            })
            
        except Exception as e:
            logger.error(f"Payout scheduler failed: {e}", exc_info=True)
            results.append({
                "action": "scheduler_error",
                "error": str(e)
            })
        
        return results
    
    def get_pending_payouts(self) -> List[Dict[str, Any]]:
        """Get all pending payout proposals."""
        payouts = self.db.query(Payout).filter(
            Payout.status.in_(["proposed", "scheduled", "processing"])
        ).order_by(Payout.created_at.desc()).all()
        
        return [
            {
                "id": p.id,
                "provider": p.provider,
                "currency": p.currency,
                "amount": p.amount,
                "status": p.status,
                "method": p.method,
                "scheduled_for": p.scheduled_for.isoformat() if p.scheduled_for else None,
                "executed_at": p.executed_at.isoformat() if p.executed_at else None,
                "external_ref": p.external_ref,
                "created_at": p.created_at.isoformat(),
                "meta": p.meta
            }
            for p in payouts
        ]
    
    async def mark_payout_paid(self, payout_id: int, external_ref: str = None) -> bool:
        """Mark a payout as paid (for manual confirmation)."""
        payout = self.db.query(Payout).filter(Payout.id == payout_id).first()
        if not payout:
            return False
        
        payout.status = "paid"
        payout.executed_at = datetime.now(self.timezone)
        if external_ref:
            payout.external_ref = external_ref
        
        self.db.commit()
        
        logger.info(f"Marked payout {payout_id} as paid")
        return True
