"""Finance admin API endpoints."""

from typing import Dict, List, Any, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

from ..db import SessionLocal
from .treasury import TreasuryService
from .reconciliation import ReconciliationService
from .ledger import LedgerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/finance", tags=["finance"])

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_role(x_role: str = Header(None)):
    """Check user role for RBAC."""
    if not x_role or x_role not in ["viewer", "operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Invalid or missing role")
    return x_role

# Request models
class ExecutePayoutRequest(BaseModel):
    dry_run: bool = False

class MarkPayoutPaidRequest(BaseModel):
    external_ref: Optional[str] = None

@router.get("/dashboard")
async def get_finance_dashboard(
    currency: str = Query("EUR"),
    db: Session = Depends(get_db),
    role: str = Depends(check_role)
):
    """Get finance dashboard data."""
    if role not in ["viewer", "operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        ledger = LedgerService(db)
        treasury = TreasuryService(db)
        
        # Get balances
        balances = ledger.get_balances_by_currency(currency)
        cash_balances = treasury.get_cash_balances()
        
        # Get pending payouts
        pending_payouts = treasury.get_pending_payouts()
        
        # Calculate metrics
        total_cash = balances.get(f"platform:cash:{currency.lower()}", 0)
        total_receivables = balances.get(f"platform:receivables:{currency.lower()}", 0)
        total_fees = balances.get(f"platform:fees:{currency.lower()}", 0)
        
        # Calculate fee rate (fees / total processed)
        total_processed = total_cash + abs(total_fees)
        fee_rate = (abs(total_fees) / max(total_processed, 1)) * 100
        
        return {
            "currency": currency,
            "balances": {
                "total_cash": total_cash,
                "total_receivables": total_receivables,
                "total_fees": abs(total_fees),
                "fee_rate_percent": round(fee_rate, 2),
                "by_account": balances
            },
            "cash_by_provider": cash_balances,
            "pending_payouts": {
                "count": len(pending_payouts),
                "total_amount": sum(p["amount"] for p in pending_payouts),
                "payouts": pending_payouts[:10]  # Latest 10
            }
        }
        
    except Exception as e:
        logger.error(f"Dashboard data retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")

@router.get("/payouts")
async def get_payouts(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    role: str = Depends(check_role)
):
    """Get payout proposals and history."""
    if role not in ["viewer", "operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        treasury = TreasuryService(db)
        
        if status:
            # Filter by status if provided
            from .models import Payout
            payouts = db.query(Payout).filter(Payout.status == status).order_by(Payout.created_at.desc()).all()
            payout_data = [
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
        else:
            payout_data = treasury.get_pending_payouts()
        
        return {
            "payouts": payout_data,
            "count": len(payout_data)
        }
        
    except Exception as e:
        logger.error(f"Payout retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve payouts")

@router.post("/payouts/schedule")
async def run_payout_scheduler(
    dry_run: bool = Query(False),
    db: Session = Depends(get_db),
    role: str = Depends(check_role)
):
    """Run payout scheduler manually."""
    if role not in ["admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        treasury = TreasuryService(db)
        results = await treasury.run_payout_scheduler(dry_run=dry_run)
        
        return {
            "dry_run": dry_run,
            "results": results,
            "summary": {
                "proposals_created": len([r for r in results if r.get("action") == "created_payout_proposal"]),
                "would_create": len([r for r in results if r.get("action") == "would_create_payout"]),
                "errors": len([r for r in results if "error" in r])
            }
        }
        
    except Exception as e:
        logger.error(f"Payout scheduler failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Payout scheduler failed")

@router.post("/payouts/{payout_id}/execute")
async def execute_payout(
    payout_id: int,
    request: ExecutePayoutRequest,
    db: Session = Depends(get_db),
    role: str = Depends(check_role)
):
    """Execute a payout proposal."""
    if role not in ["admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        treasury = TreasuryService(db)
        result = await treasury.execute_payout(payout_id, request.dry_run)
        
        return result
        
    except Exception as e:
        logger.error(f"Payout execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payouts/{payout_id}/mark-paid")
async def mark_payout_paid(
    payout_id: int,
    request: MarkPayoutPaidRequest,
    db: Session = Depends(get_db),
    role: str = Depends(check_role)
):
    """Mark payout as paid (manual confirmation)."""
    if role not in ["admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        treasury = TreasuryService(db)
        success = await treasury.mark_payout_paid(payout_id, request.external_ref)
        
        if not success:
            raise HTTPException(status_code=404, detail="Payout not found")
        
        return {"status": "marked_paid", "payout_id": payout_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mark payout paid failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to mark payout as paid")

@router.get("/reconciliation/{provider}")
async def get_reconciliation(
    provider: str,
    target_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    role: str = Depends(check_role)
):
    """Get reconciliation report for a provider and date."""
    if role not in ["viewer", "operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if provider not in ["stripe", "paypal"]:
        raise HTTPException(status_code=400, detail="Invalid provider")
    
    try:
        reco = ReconciliationService(db)
        
        # Parse date
        if target_date:
            try:
                parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            parsed_date = date.today()
        
        # Run reconciliation
        if provider == "stripe":
            result = await reco.reconcile_stripe(parsed_date)
        else:
            result = await reco.reconcile_paypal(parsed_date)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reconciliation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Reconciliation failed")

@router.get("/reconciliation/{provider}/export")
async def export_reconciliation_csv(
    provider: str,
    target_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    role: str = Depends(check_role)
):
    """Export reconciliation report as CSV."""
    if role not in ["viewer", "operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if provider not in ["stripe", "paypal"]:
        raise HTTPException(status_code=400, detail="Invalid provider")
    
    try:
        reco = ReconciliationService(db)
        
        # Parse date
        if target_date:
            try:
                parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            parsed_date = date.today()
        
        # Run reconciliation
        if provider == "stripe":
            result = await reco.reconcile_stripe(parsed_date)
        else:
            result = await reco.reconcile_paypal(parsed_date)
        
        # Export to CSV
        csv_content = reco.export_reconciliation_csv(result)
        
        from fastapi.responses import Response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=reconciliation_{provider}_{parsed_date.isoformat()}.csv"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="CSV export failed")

@router.post("/reconciliation/daily")
async def run_daily_reconciliation(
    target_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    role: str = Depends(check_role)
):
    """Run daily reconciliation for all providers."""
    if role not in ["operator", "admin", "dg_ai"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        reco = ReconciliationService(db)
        
        # Parse date
        if target_date:
            try:
                parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            parsed_date = date.today()
        
        result = await reco.run_daily_reconciliation(parsed_date)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Daily reconciliation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Daily reconciliation failed")
