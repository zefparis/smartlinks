
from __future__ import annotations
import logging
import os
from dotenv import load_dotenv
from .storage import init_db, upsert_offer, upsert_segment, upsert_creator, record_click
from .config import PUBLIC_BASE_URL
from .db import Base, engine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create all tables in the database"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def seed_initial_data():
    """Seed the database with initial data"""
    try:
        # Seed segments
        logger.info("Seeding segments...")
        upsert_segment("FR:mobile", "FR", "mobile")
        upsert_segment("FR:desktop", "FR", "desktop")
        
        # Seed a default creator
        logger.info("Seeding default creator...")
        upsert_creator("default_creator")
        
        # Seed offers
        logger.info("Seeding offers...")
        base = PUBLIC_BASE_URL or "https://example.org"
        upsert_offer("offer_a", "Offer A", f"{base}/a")
        upsert_offer("offer_b", "Offer B", f"{base}/b")
        upsert_offer("offer_c", "Offer C", f"{base}/c")
        
        logger.info("Database seeded successfully")
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        raise

def main():
    """Initialize the database and seed with initial data"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Create tables
        logger.info("Creating database tables...")
        create_tables()
        
        # Seed initial data
        logger.info("Seeding initial data...")
        seed_initial_data()
        
        print("✅ Database initialized and seeded successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

if __name__ == "__main__":
    main()
