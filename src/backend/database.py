"""
Database configuration and connection management for Railway PostgreSQL
"""

import os
import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# Database URL from Railway environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback construction from individual components
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "smartlinks")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Create engine with connection pooling for production
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("DEBUG", "false").lower() == "true"
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database tables"""
    try:
        logger.info("🗄️ Initializing database...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
