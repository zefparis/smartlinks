
from __future__ import annotations
import time
import math
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from .config import load_policy
from .storage import epc_for_segment, set_payout_rate, connect, init_db, upsert_segment
from .db import SessionLocal, engine

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('autopilot.log')
    ]
)
logger = logging.getLogger(__name__)

def segments(session: Session) -> List[str]:
    """Get all segment IDs from the database."""
    try:
        logger.info("Fetching all segments")
        result = session.execute(text("SELECT segment_id FROM segments"))
        return [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching segments: {e}")
        return []

def fraud_rate(session: Session, seg_id: str, horizon_h: int = 72) -> float:
    """Calculate fraud rate for a segment."""
    try:
        since = int(time.time()) - horizon_h * 3600
        logger.debug(f"Calculating fraud rate for segment {seg_id} since {since}")
        
        result = session.execute(
            text("""
                SELECT COALESCE(AVG(CASE WHEN risk >= :threshold THEN 1.0 ELSE 0.0 END), 0.0)
                FROM clicks 
                WHERE ts >= :since AND segment_id = :seg_id
            """),
            {"threshold": POLICY.fraud_threshold, "since": since, "seg_id": seg_id}
        )
        row = result.fetchone()
        return float(row[0] or 0.0)
    except Exception as e:
        logger.error(f"Error calculating fraud rate for segment {seg_id}: {e}")
        return 0.0

def payout_formula(epc_net: float, fraud_r: float) -> float:
    """Calculate payout using the formula."""
    try:
        # Risk discount = k_sigma * 0 (no sigma here) + k_fraud * fraud_r
        disc = POLICY.k_fraud * fraud_r
        raw = POLICY.alpha * epc_net * (1.0 - disc) - POLICY.buffer_eur
        return max(POLICY.min_eur, min(POLICY.max_eur, round(raw, 2)))
    except Exception as e:
        logger.error(f"Error in payout formula: {e}")
        return POLICY.min_eur

def loop_once():
    """Run one iteration of the autopilot loop."""
    session = None
    try:
        session = SessionLocal()
        logger.info("Starting autopilot iteration")
        
        for seg in segments(session):
            try:
                logger.info(f"Processing segment: {seg}")
                # Pass the session to all functions that need it
                epc = epc_for_segment(seg, horizon_hours=72, db=session)
                fr = fraud_rate(session, seg)
                payout = payout_formula(epc, fr)
                logger.info(f"Setting payout for {seg}: {payout}")
                set_payout_rate(seg, payout, int(time.time()), db=session)
            except Exception as seg_error:
                logger.error(f"Error processing segment {seg}: {seg_error}", exc_info=True)
                continue
                
    except Exception as e:
        logger.error(f"Error in autopilot loop: {e}", exc_info=True)
        if session:
            session.rollback()
    finally:
        if session:
            session.close()
            logger.info("DB session closed")

def run_forever(interval_sec: int = 3600):
    """Run the autopilot in an infinite loop."""
    logger.info(f"Starting autopilot with interval: {interval_sec} seconds")
    while True:
        try:
            loop_start = time.time()
            loop_once()
            duration = time.time() - loop_start
            logger.info(f"Payout rates updated @ {time.strftime('%F %T')} (took {duration:.2f}s)")
        except Exception as e:
            logger.error(f"Error in autopilot: {e}", exc_info=True)
        
        # Sleep for the remaining interval time
        time_elapsed = time.time() - loop_start
        sleep_time = max(0, interval_sec - time_elapsed)
        if sleep_time > 0:
            logger.debug(f"Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

# Load policy once at module level
POLICY = load_policy()

def main():
    """Initialize the database and start the autopilot."""
    logger.info("Starting SmartLinks Autopilot")
    
    # Ensure DB schema and default segments are present
    try:
        logger.info("Initializing database...")
        init_db()
        
        # Ensure default segments exist for FR mobile/desktop
        with SessionLocal() as session:
            logger.info("Ensuring default segments exist")
            try:
                upsert_segment("FR:mobile", "FR", "mobile")
                upsert_segment("FR:desktop", "FR", "desktop")
                session.commit()
                logger.info("Default segments ensured")
            except Exception as e:
                session.rollback()
                logger.error(f"Error ensuring default segments: {e}", exc_info=True)
                raise
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}", exc_info=True)
        return 1

    # Start the autopilot
    try:
        run_forever(600)  # every 10 minutes in dev
    except KeyboardInterrupt:
        logger.info("Autopilot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error in autopilot: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
