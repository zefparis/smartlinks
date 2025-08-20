"""Reconciliation engine for Stripe & PayPal."""

import os
import csv
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import httpx
import logging

from .models import Payment, Refund, Fee, Entry, ProviderEvent
from .ledger import LedgerService

logger = logging.getLogger(__name__)

class ReconciliationService:
    """Reconciliation service for payment providers."""
    
    def __init__(self, db: Session):
        self.db = db
        self.ledger = LedgerService(db)
    
    async def reconcile_stripe(self, target_date: date) -> Dict[str, Any]:
        """Reconcile Stripe transactions for a specific date."""
        stripe_secret = os.getenv("STRIPE_SECRET_KEY")
        if not stripe_secret:
            raise ValueError("Stripe secret key not configured")
        
        # Fetch Stripe balance transactions
        stripe_transactions = await self._fetch_stripe_transactions(target_date)
        
        # Get our ledger entries for the same date
        ledger_entries = self._get_ledger_entries_for_date("stripe_cards", target_date)
        
        # Perform reconciliation
        return self._reconcile_transactions(
            "stripe_cards",
            stripe_transactions,
            ledger_entries,
            target_date
        )
    
    async def reconcile_paypal(self, target_date: date) -> Dict[str, Any]:
        """Reconcile PayPal transactions for a specific date."""
        # Fetch PayPal transactions
        paypal_transactions = await self._fetch_paypal_transactions(target_date)
        
        # Get our ledger entries for the same date
        ledger_entries = self._get_ledger_entries_for_date("paypal_checkout", target_date)
        
        # Perform reconciliation
        return self._reconcile_transactions(
            "paypal_checkout",
            paypal_transactions,
            ledger_entries,
            target_date
        )
    
    async def _fetch_stripe_transactions(self, target_date: date) -> List[Dict[str, Any]]:
        """Fetch Stripe balance transactions for a date."""
        stripe_secret = os.getenv("STRIPE_SECRET_KEY")
        
        # Convert date to timestamps
        start_ts = int(datetime.combine(target_date, datetime.min.time()).timestamp())
        end_ts = int(datetime.combine(target_date, datetime.max.time()).timestamp())
        
        params = {
            "created[gte]": str(start_ts),
            "created[lte]": str(end_ts),
            "limit": "100"
        }
        
        headers = {
            "Authorization": f"Bearer {stripe_secret}",
        }
        
        transactions = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.stripe.com/v1/balance_transactions"
            
            while url:
                response = await client.get(url, headers=headers, params=params if url == "https://api.stripe.com/v1/balance_transactions" else None)
                response.raise_for_status()
                
                data = response.json()
                transactions.extend(data.get("data", []))
                
                # Handle pagination
                if data.get("has_more"):
                    url = f"https://api.stripe.com/v1/balance_transactions?starting_after={data['data'][-1]['id']}&created[gte]={start_ts}&created[lte]={end_ts}&limit=100"
                else:
                    url = None
        
        return transactions
    
    async def _fetch_paypal_transactions(self, target_date: date) -> List[Dict[str, Any]]:
        """Fetch PayPal transactions for a date."""
        from .providers.paypal_provider import PayPalProvider
        
        provider = PayPalProvider()
        
        # PayPal transaction search API
        start_date = target_date.strftime("%Y-%m-%dT00:00:00Z")
        end_date = target_date.strftime("%Y-%m-%dT23:59:59Z")
        
        search_data = {
            "transaction_date": f"{start_date}/{end_date}",
            "fields": "all",
            "page_size": "500",
            "page": "1"
        }
        
        try:
            result = await provider._make_request(
                "POST",
                "/v1/reporting/transactions",
                search_data
            )
            
            return result.get("transaction_details", [])
            
        except Exception as e:
            logger.error(f"PayPal transaction fetch failed: {e}")
            return []
    
    def _get_ledger_entries_for_date(self, provider: str, target_date: date) -> List[Dict[str, Any]]:
        """Get ledger entries for a provider and date."""
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        # Get payments
        payments = self.db.query(Payment).filter(
            and_(
                Payment.provider == provider,
                Payment.created_at >= start_datetime,
                Payment.created_at <= end_datetime
            )
        ).all()
        
        # Get refunds
        refunds = self.db.query(Refund).filter(
            and_(
                Refund.provider == provider,
                Refund.created_at >= start_datetime,
                Refund.created_at <= end_datetime
            )
        ).all()
        
        # Get fees
        fees = self.db.query(Fee).filter(
            and_(
                Fee.provider == provider,
                Fee.created_at >= start_datetime,
                Fee.created_at <= end_datetime
            )
        ).all()
        
        entries = []
        
        # Convert to common format
        for payment in payments:
            entries.append({
                "type": "payment",
                "id": payment.id,
                "provider_id": payment.provider_payment_id,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status,
                "timestamp": payment.created_at
            })
        
        for refund in refunds:
            entries.append({
                "type": "refund",
                "id": refund.id,
                "provider_id": refund.provider_refund_id,
                "amount": -refund.amount,  # Negative for refunds
                "currency": refund.currency,
                "status": refund.status,
                "timestamp": refund.created_at
            })
        
        for fee in fees:
            entries.append({
                "type": "fee",
                "id": fee.id,
                "provider_id": None,
                "amount": fee.amount,
                "currency": fee.currency,
                "status": "recorded",
                "timestamp": fee.created_at
            })
        
        return entries
    
    def _reconcile_transactions(self, provider: str, provider_transactions: List[Dict], 
                              ledger_entries: List[Dict], target_date: date) -> Dict[str, Any]:
        """Perform reconciliation between provider and ledger data."""
        matched = []
        missing_in_ledger = []
        missing_in_provider = []
        mismatched = []
        
        # Create lookup maps
        provider_map = {}
        for tx in provider_transactions:
            if provider == "stripe_cards":
                key = tx.get("source")  # Payment intent ID or similar
                amount = tx.get("amount", 0)
            else:  # PayPal
                key = tx.get("transaction_info", {}).get("transaction_id")
                amount = int(float(tx.get("transaction_info", {}).get("transaction_amount", {}).get("value", "0")) * 100)
            
            if key:
                provider_map[key] = {
                    "amount": amount,
                    "currency": tx.get("currency", "EUR").upper(),
                    "raw": tx
                }
        
        ledger_map = {}
        for entry in ledger_entries:
            key = entry["provider_id"]
            if key:
                ledger_map[key] = entry
        
        # Find matches
        for provider_id, provider_data in provider_map.items():
            if provider_id in ledger_map:
                ledger_data = ledger_map[provider_id]
                
                # Check if amounts match
                if abs(provider_data["amount"] - abs(ledger_data["amount"])) < 1:  # Allow 1 cent variance
                    matched.append({
                        "provider_id": provider_id,
                        "provider_amount": provider_data["amount"],
                        "ledger_amount": ledger_data["amount"],
                        "currency": provider_data["currency"],
                        "type": ledger_data["type"]
                    })
                else:
                    mismatched.append({
                        "provider_id": provider_id,
                        "provider_amount": provider_data["amount"],
                        "ledger_amount": ledger_data["amount"],
                        "currency": provider_data["currency"],
                        "variance": provider_data["amount"] - abs(ledger_data["amount"])
                    })
            else:
                missing_in_ledger.append({
                    "provider_id": provider_id,
                    "amount": provider_data["amount"],
                    "currency": provider_data["currency"],
                    "raw": provider_data["raw"]
                })
        
        # Find ledger entries missing in provider
        for provider_id, ledger_data in ledger_map.items():
            if provider_id and provider_id not in provider_map:
                missing_in_provider.append({
                    "provider_id": provider_id,
                    "amount": ledger_data["amount"],
                    "currency": ledger_data["currency"],
                    "type": ledger_data["type"]
                })
        
        # Calculate metrics
        total_provider_amount = sum(tx["amount"] for tx in provider_map.values())
        total_ledger_amount = sum(abs(entry["amount"]) for entry in ledger_entries)
        matched_amount = sum(item["provider_amount"] for item in matched)
        
        match_rate = (len(matched) / max(len(provider_transactions), 1)) * 100
        
        return {
            "date": target_date.isoformat(),
            "provider": provider,
            "summary": {
                "total_provider_transactions": len(provider_transactions),
                "total_ledger_entries": len(ledger_entries),
                "matched_count": len(matched),
                "missing_in_ledger_count": len(missing_in_ledger),
                "missing_in_provider_count": len(missing_in_provider),
                "mismatched_count": len(mismatched),
                "match_rate_percent": round(match_rate, 2),
                "total_provider_amount": total_provider_amount,
                "total_ledger_amount": total_ledger_amount,
                "matched_amount": matched_amount
            },
            "details": {
                "matched": matched,
                "missing_in_ledger": missing_in_ledger,
                "missing_in_provider": missing_in_provider,
                "mismatched": mismatched
            }
        }
    
    def export_reconciliation_csv(self, reconciliation_data: Dict[str, Any]) -> str:
        """Export reconciliation results to CSV format."""
        output = []
        
        # Header
        output.append("Type,Provider ID,Provider Amount,Ledger Amount,Currency,Variance,Status")
        
        # Matched transactions
        for item in reconciliation_data["details"]["matched"]:
            output.append(f"Matched,{item['provider_id']},{item['provider_amount']},{item['ledger_amount']},{item['currency']},0,OK")
        
        # Missing in ledger
        for item in reconciliation_data["details"]["missing_in_ledger"]:
            output.append(f"Missing in Ledger,{item['provider_id']},{item['amount']},,{item['currency']},{item['amount']},ALERT")
        
        # Missing in provider
        for item in reconciliation_data["details"]["missing_in_provider"]:
            output.append(f"Missing in Provider,{item['provider_id']},{item['amount']},{item['amount']},{item['currency']},{item['amount']},ALERT")
        
        # Mismatched
        for item in reconciliation_data["details"]["mismatched"]:
            output.append(f"Mismatched,{item['provider_id']},{item['provider_amount']},{item['ledger_amount']},{item['currency']},{item['variance']},WARNING")
        
        return "\n".join(output)
    
    async def run_daily_reconciliation(self, target_date: date = None) -> Dict[str, Any]:
        """Run reconciliation for both providers for a given date."""
        if not target_date:
            target_date = date.today()
        
        results = {
            "date": target_date.isoformat(),
            "providers": {}
        }
        
        try:
            # Reconcile Stripe
            stripe_result = await self.reconcile_stripe(target_date)
            results["providers"]["stripe"] = stripe_result
        except Exception as e:
            logger.error(f"Stripe reconciliation failed: {e}")
            results["providers"]["stripe"] = {"error": str(e)}
        
        try:
            # Reconcile PayPal
            paypal_result = await self.reconcile_paypal(target_date)
            results["providers"]["paypal"] = paypal_result
        except Exception as e:
            logger.error(f"PayPal reconciliation failed: {e}")
            results["providers"]["paypal"] = {"error": str(e)}
        
        # Overall summary
        total_matched = 0
        total_transactions = 0
        
        for provider_data in results["providers"].values():
            if "summary" in provider_data:
                total_matched += provider_data["summary"]["matched_count"]
                total_transactions += provider_data["summary"]["total_provider_transactions"]
        
        overall_match_rate = (total_matched / max(total_transactions, 1)) * 100
        
        results["overall_summary"] = {
            "total_transactions": total_transactions,
            "total_matched": total_matched,
            "overall_match_rate_percent": round(overall_match_rate, 2)
        }
        
        return results
