"""
Dependency injection for the SmartLinks DG API.
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import logging
import os

from .ai.supervisor import IASupervisor, OperationMode

logger = logging.getLogger(__name__)

# Global instance of the IASupervisor
_ia_supervisor = None

def get_settings():
    """Get AI supervisor application settings."""
    return {
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "openai_api_base": os.getenv("OPENAI_API_BASE")
    }

def init_ia_supervisor() -> None:
    """Initialize the global IASupervisor instance."""
    global _ia_supervisor
    
    if _ia_supervisor is not None:
        return
    
    try:
        logger.info("Initializing IASupervisor...")
        _ia_supervisor = IASupervisor(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            algorithm_paths=None,  # Utilise les chemins par défaut
            initial_mode=OperationMode.AUTO
        )
        logger.info("IASupervisor initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize IASupervisor: {e}", exc_info=True)
        raise

def get_ia_supervisor() -> IASupervisor:
    """Get the global IASupervisor instance."""
    if _ia_supervisor is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="IASupervisor not initialized"
        )
    return _ia_supervisor

@contextmanager
def ia_supervisor_context() -> Generator[IASupervisor, None, None]:
    """Context manager for the IASupervisor."""
    try:
        init_ia_supervisor()
        yield get_ia_supervisor()
    finally:
        # Add any cleanup code here if needed
        pass

def get_current_ia_supervisor(
    supervisor: IASupervisor = Depends(get_ia_supervisor)
) -> IASupervisor:
    """Dependency that returns the current IASupervisor instance."""
    return supervisor

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smartlinks.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Database dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session_factory():
    """Get database session factory."""
    return SessionLocal
