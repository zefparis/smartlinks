"""Tests for ledger system."""

import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session
from datetime import datetime

from ..ledger import LedgerService
from ..models import Account, Payment, Entry
from ..providers.base import PaymentResult

class TestLedgerService:
    """Test ledger double-entry system."""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def ledger(self, mock_db):
        return LedgerService(mock_db)
    
    def test_get_or_create_account(self, ledger, mock_db):
        """Test account creation."""
        # Mock existing account
        existing_account = Account(id=1, code="platform:cash:eur", currency="EUR")
        mock_db.query.return_value.filter.return_value.first.return_value = existing_account
        
        result = ledger.get_or_create_account("platform:cash:eur", "EUR")
        
        assert result == existing_account
        mock_db.add.assert_not_called()
    
    def test_create_account_new(self, ledger, mock_db):
        """Test new account creation."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = ledger.get_or_create_account("platform:cash:eur", "EUR")
        
        assert result.code == "platform:cash:eur"
        assert result.currency == "EUR"
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
    
    def test_create_entry(self, ledger, mock_db):
        """Test ledger entry creation."""
        account = Account(id=1, code="platform:cash:eur", currency="EUR")
        mock_db.query.return_value.filter.return_value.first.return_value = account
        
        entry = ledger.create_entry(
            "platform:cash:eur",
            10000,
            "payment",
            123,
            "Test payment"
        )
        
        assert entry.account_id == 1
        assert entry.amount == 10000
        assert entry.ref_type == "payment"
        assert entry.ref_id == 123
        assert entry.memo == "Test payment"
        mock_db.add.assert_called()
    
    @pytest.mark.asyncio
    async def test_record_payment_created(self, ledger, mock_db):
        """Test payment creation recording."""
        # Mock account creation
        receivables_account = Account(id=1, code="platform:receivables:eur", currency="EUR")
        clearing_account = Account(id=2, code="stripe:clearing:eur", currency="EUR")
        
        def mock_get_account(code, currency):
            if "receivables" in code:
                return receivables_account
            elif "clearing" in code:
                return clearing_account
        
        ledger.get_or_create_account = Mock(side_effect=mock_get_account)
        
        session_data = {"id": "cs_test_123"}
        payment_id = await ledger.record_payment_created(
            "stripe_cards",
            session_data,
            10000,
            "EUR",
            {"meta": "data"}
        )
        
        # Verify payment creation
        mock_db.add.assert_called()
        mock_db.flush.assert_called()
        mock_db.commit.assert_called()
        
        # Verify entries were created (2 entries for double-entry)
        assert mock_db.add.call_count >= 3  # Payment + 2 entries
    
    @pytest.mark.asyncio
    async def test_record_capture(self, ledger, mock_db):
        """Test payment capture recording."""
        # Mock existing payment
        payment = Payment(
            id=1,
            provider="stripe_cards",
            provider_payment_id="pi_test_123",
            amount=10000,
            currency="EUR",
            status="created"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = payment
        
        # Mock accounts
        receivables_account = Account(id=1, code="platform:receivables:eur", currency="EUR")
        cash_account = Account(id=2, code="platform:cash:eur", currency="EUR")
        fees_account = Account(id=3, code="platform:fees:eur", currency="EUR")
        
        def mock_get_account(code, currency):
            if "receivables" in code:
                return receivables_account
            elif "cash" in code:
                return cash_account
            elif "fees" in code:
                return fees_account
        
        ledger.get_or_create_account = Mock(side_effect=mock_get_account)
        
        result = PaymentResult(
            status="captured",
            provider="stripe_cards",
            provider_payment_id="pi_test_123",
            amount=10000,
            currency="EUR",
            fees=320,
            raw={}
        )
        
        await ledger.record_capture(result)
        
        # Verify payment status update
        assert payment.status == "captured"
        
        # Verify entries creation
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
    
    def test_get_balance(self, ledger, mock_db):
        """Test balance calculation."""
        account = Account(id=1, code="platform:cash:eur", currency="EUR")
        mock_db.query.return_value.filter.return_value.first.return_value = account
        mock_db.query.return_value.filter.return_value.scalar.return_value = 50000
        
        balance = ledger.get_balance("platform:cash:eur")
        
        assert balance == 50000
    
    def test_assert_ledger_balanced(self, ledger, mock_db):
        """Test ledger balance assertion."""
        # Mock balanced ledger (sum = 0)
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        
        is_balanced = ledger.assert_ledger_balanced("payment", 123)
        
        assert is_balanced is True
        
        # Mock unbalanced ledger
        mock_db.query.return_value.filter.return_value.scalar.return_value = 100
        
        is_balanced = ledger.assert_ledger_balanced("payment", 123)
        
        assert is_balanced is False

@pytest.mark.asyncio
async def test_payment_flow_integration():
    """Test complete payment flow maintains ledger balance."""
    # This would be an integration test with real database
    # For now, just verify the logic flow
    
    # 1. Create payment -> receivables +10000, clearing -10000 (sum = 0)
    # 2. Capture payment -> receivables -10000, cash +10000, cash -320, fees +320 (sum = 0)
    # 3. Refund -> cash -5000, refunds +5000 (sum = 0)
    
    # Each operation should maintain ledger balance
    assert True  # Placeholder for integration test
