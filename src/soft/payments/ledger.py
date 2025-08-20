"""Double-entry ledger system for payments."""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import logging

from .models import Account, Payment, Refund, Fee, Entry, ProviderEvent
from .providers.base import PaymentResult

logger = logging.getLogger(__name__)

class LedgerService:
    """Double-entry bookkeeping service."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_account(self, code: str, currency: str) -> Account:
        """Get or create account by code."""
        account = self.db.query(Account).filter(Account.code == code).first()
        if not account:
            account = Account(code=code, currency=currency)
            self.db.add(account)
            self.db.flush()
        return account
    
    def create_entry(self, account_code: str, amount: int, ref_type: str, 
                    ref_id: int, memo: str = None, currency: str = "EUR") -> Entry:
        """Create a ledger entry."""
        account = self.get_or_create_account(account_code, currency)
        entry = Entry(
            account_id=account.id,
            amount=amount,
            ref_type=ref_type,
            ref_id=ref_id,
            memo=memo
        )
        self.db.add(entry)
        return entry
    
    async def record_payment_created(self, provider: str, session_data: Dict[str, Any], 
                                   amount: int, currency: str, meta: Dict[str, Any] = None) -> int:
        """Record payment creation and initial ledger entries."""
        # Create payment record
        payment = Payment(
            provider=provider,
            provider_payment_id=session_data.get("id"),
            amount=amount,
            currency=currency,
            status="created",
            meta=meta or {}
        )
        self.db.add(payment)
        self.db.flush()
        
        # Create receivable entry (what we expect to receive)
        self.create_entry(
            f"platform:receivables:{currency.lower()}",
            amount,  # Credit receivables
            "payment",
            payment.id,
            f"Payment created via {provider}",
            currency
        )
        
        # Create clearing entry (provider owes us)
        self.create_entry(
            f"{provider.split('_')[0]}:clearing:{currency.lower()}",
            -amount,  # Debit clearing
            "payment", 
            payment.id,
            f"Payment pending via {provider}",
            currency
        )
        
        self.db.commit()
        return payment.id
    
    async def record_capture(self, result: PaymentResult) -> None:
        """Record payment capture and move money to cash."""
        # Find existing payment
        payment = self.db.query(Payment).filter(
            Payment.provider_payment_id == result["provider_payment_id"]
        ).first()
        
        if not payment:
            logger.error(f"Payment not found for capture: {result['provider_payment_id']}")
            return
        
        # Update payment status
        payment.status = result["status"]
        payment.updated_at = datetime.now()
        
        currency = result["currency"].lower()
        amount = result["amount"]
        
        # Move from receivables to cash
        self.create_entry(
            f"platform:receivables:{currency}",
            -amount,  # Debit receivables (reduce what we expect)
            "payment",
            payment.id,
            "Payment captured - receivables to cash"
        )
        
        self.create_entry(
            f"platform:cash:{currency}",
            amount,  # Credit cash (increase our cash)
            "payment",
            payment.id,
            "Payment captured - cash received"
        )
        
        # Record fees if present
        if result.get("fees"):
            fee_amount = result["fees"]
            
            # Create fee record
            fee = Fee(
                payment_id=payment.id,
                provider=result["provider"],
                amount=fee_amount,
                currency=result["currency"],
                detail={"raw": result.get("raw", {})}
            )
            self.db.add(fee)
            self.db.flush()
            
            # Record fee entries
            self.create_entry(
                f"platform:cash:{currency}",
                -fee_amount,  # Debit cash (reduce cash by fee)
                "fee",
                fee.id,
                f"Provider fee - {result['provider']}"
            )
            
            self.create_entry(
                f"platform:fees:{currency}",
                fee_amount,  # Credit fees (expense account)
                "fee",
                fee.id,
                f"Provider fee expense - {result['provider']}"
            )
        
        self.db.commit()
    
    async def record_refund(self, result: PaymentResult, original_payment_id: int = None) -> None:
        """Record refund and reverse ledger entries."""
        # Find original payment if not provided
        if not original_payment_id:
            payment = self.db.query(Payment).filter(
                Payment.provider_payment_id == result["provider_payment_id"]
            ).first()
            if payment:
                original_payment_id = payment.id
        
        if not original_payment_id:
            logger.error(f"Cannot find original payment for refund: {result['provider_payment_id']}")
            return
        
        # Create refund record
        refund = Refund(
            payment_id=original_payment_id,
            provider=result["provider"],
            provider_refund_id=result["provider_payment_id"],
            amount=result["amount"],
            currency=result["currency"],
            status=result["status"]
        )
        self.db.add(refund)
        self.db.flush()
        
        currency = result["currency"].lower()
        amount = result["amount"]
        
        # Reverse cash entries
        self.create_entry(
            f"platform:cash:{currency}",
            -amount,  # Debit cash (reduce our cash)
            "refund",
            refund.id,
            "Refund processed - cash returned"
        )
        
        self.create_entry(
            f"platform:refunds:{currency}",
            amount,  # Credit refunds (expense account)
            "refund",
            refund.id,
            "Refund expense"
        )
        
        self.db.commit()
    
    async def record_payout(self, provider: str, currency: str, amount: int, 
                          method: str, external_ref: str = None) -> int:
        """Record payout and move cash to bank."""
        from .models import Payout
        
        payout = Payout(
            provider=provider,
            currency=currency,
            amount=amount,
            status="processing",
            method=method,
            external_ref=external_ref,
            executed_at=datetime.now()
        )
        self.db.add(payout)
        self.db.flush()
        
        currency_lower = currency.lower()
        
        # Move cash to bank
        self.create_entry(
            f"platform:cash:{currency_lower}",
            -amount,  # Debit cash
            "payout",
            payout.id,
            f"Payout to bank via {method}"
        )
        
        self.create_entry(
            f"platform:bank:{currency_lower}",
            amount,  # Credit bank
            "payout",
            payout.id,
            f"Bank transfer via {method}"
        )
        
        self.db.commit()
        return payout.id
    
    def get_balance(self, account_code: str) -> int:
        """Get current balance for an account."""
        account = self.db.query(Account).filter(Account.code == account_code).first()
        if not account:
            return 0
        
        balance = self.db.query(func.sum(Entry.amount)).filter(
            Entry.account_id == account.id
        ).scalar()
        
        return balance or 0
    
    def get_balances_by_currency(self, currency: str) -> Dict[str, int]:
        """Get all balances for a specific currency."""
        balances = {}
        
        accounts = self.db.query(Account).filter(
            Account.currency == currency.upper()
        ).all()
        
        for account in accounts:
            balance = self.db.query(func.sum(Entry.amount)).filter(
                Entry.account_id == account.id
            ).scalar()
            balances[account.code] = balance or 0
        
        return balances
    
    def assert_ledger_balanced(self, ref_type: str, ref_id: int) -> bool:
        """Assert that all entries for a reference sum to zero."""
        total = self.db.query(func.sum(Entry.amount)).filter(
            Entry.ref_type == ref_type,
            Entry.ref_id == ref_id
        ).scalar()
        
        is_balanced = (total or 0) == 0
        if not is_balanced:
            logger.error(f"Ledger imbalance for {ref_type}:{ref_id} = {total}")
        
        return is_balanced
    
    async def store_provider_event(self, provider: str, event_type: str, 
                                 payload: Dict[str, Any], signature_valid: bool = False,
                                 provider_id: str = None) -> int:
        """Store raw provider event for audit."""
        event = ProviderEvent(
            provider=provider,
            event_type=event_type,
            payload=payload,
            signature_valid=signature_valid,
            provider_id=provider_id
        )
        self.db.add(event)
        self.db.flush()
        self.db.commit()
        return event.id

# Initialize default accounts
async def seed_accounts(db: Session):
    """Seed default chart of accounts."""
    ledger = LedgerService(db)
    
    default_accounts = [
        # Platform accounts
        ("platform:receivables:eur", "EUR"),
        ("platform:cash:eur", "EUR"),
        ("platform:revenue:eur", "EUR"),
        ("platform:fees:eur", "EUR"),
        ("platform:refunds:eur", "EUR"),
        ("platform:bank:eur", "EUR"),
        
        # Provider clearing accounts
        ("stripe:clearing:eur", "EUR"),
        ("paypal:clearing:eur", "EUR"),
        
        # USD accounts
        ("platform:receivables:usd", "USD"),
        ("platform:cash:usd", "USD"),
        ("platform:revenue:usd", "USD"),
        ("platform:fees:usd", "USD"),
        ("platform:refunds:usd", "USD"),
        ("platform:bank:usd", "USD"),
        ("stripe:clearing:usd", "USD"),
        ("paypal:clearing:usd", "USD"),
    ]
    
    for code, currency in default_accounts:
        ledger.get_or_create_account(code, currency)
    
    db.commit()
    logger.info(f"Seeded {len(default_accounts)} default accounts")
