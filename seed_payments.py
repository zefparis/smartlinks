#!/usr/bin/env python3
"""Seed payment accounts and test the payment system."""

import sys
import os
from pathlib import Path

# Add src to PYTHONPATH
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

from sqlalchemy.orm import Session
from soft.db import SessionLocal
from soft.payments.ledger import seed_accounts
from soft.payments.models import Account
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Seed payment accounts."""
    db = SessionLocal()
    
    try:
        logger.info("Seeding payment accounts...")
        
        # Check if accounts already exist
        existing_count = db.query(Account).count()
        if existing_count > 0:
            logger.info(f"Found {existing_count} existing accounts, skipping seed")
            return
        
        # Seed accounts
        import asyncio
        asyncio.run(seed_accounts(db))
        
        # Verify seeding
        final_count = db.query(Account).count()
        logger.info(f"Successfully seeded {final_count} accounts")
        
        # List accounts
        accounts = db.query(Account).all()
        for account in accounts:
            logger.info(f"  {account.code} ({account.currency})")
        
    except Exception as e:
        logger.error(f"Seeding failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
