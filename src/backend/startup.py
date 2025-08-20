"""
Application startup and initialization for Railway deployment
"""

import os
import logging
import asyncio
from contextlib import asynccontextmanager
from .database import init_database, test_connection
from ..soft.security.access_control import setup_default_security_rules, SecurityService
from ..soft.database import get_db

logger = logging.getLogger(__name__)

async def initialize_application():
    """Initialize all application components for production"""
    
    logger.info("🚀 Starting SmartLinks Autopilot initialization...")
    
    # 1. Test database connection
    if not test_connection():
        raise Exception("Database connection failed")
    
    # 2. Initialize database tables
    init_database()
    
    # 3. Setup default security rules
    try:
        db = next(get_db())
        await setup_default_security_rules(db)
        logger.info("✅ Security rules configured")
    except Exception as e:
        logger.error(f"❌ Security setup failed: {e}")
    
    # 4. Create default admin user if none exists
    try:
        await create_default_admin()
        logger.info("✅ Default admin user checked")
    except Exception as e:
        logger.error(f"❌ Admin user setup failed: {e}")
    
    # 5. Initialize storage directories
    setup_storage_directories()
    
    logger.info("✅ SmartLinks Autopilot initialized successfully")

async def create_default_admin():
    """Create default admin user if none exists"""
    from ..soft.security.access_control import SecurityService, UserRole
    
    db = next(get_db())
    security_service = SecurityService(db)
    
    # Check if admin exists
    from ..soft.security.access_control import User
    admin_exists = db.query(User).filter(User.role == UserRole.ADMIN.value).first()
    
    if not admin_exists:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@smartlinks.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "SmartLinks2024!")
        
        await security_service.create_user(
            email=admin_email,
            password=admin_password,
            role=UserRole.ADMIN,
            first_name="System",
            last_name="Administrator"
        )
        
        logger.info(f"✅ Default admin created: {admin_email}")
        logger.warning("⚠️ Please change the default admin password!")

def setup_storage_directories():
    """Create necessary storage directories"""
    directories = [
        os.getenv("INVOICE_STORAGE_PATH", "/app/storage/invoices"),
        os.getenv("REPORTS_STORAGE_PATH", "/app/storage/reports"),
        "/app/storage/temp",
        "/app/storage/logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"📁 Storage directory ready: {directory}")

@asynccontextmanager
async def lifespan(app):
    """FastAPI lifespan context manager"""
    # Startup
    await initialize_application()
    
    yield
    
    # Shutdown
    logger.info("🛑 SmartLinks Autopilot shutting down...")
