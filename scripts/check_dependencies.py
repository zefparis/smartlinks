#!/usr/bin/env python3
"""
Dependency checker script for SmartLinks Autopilot backend.
This script checks if all required Python packages are installed and available.
"""

import sys
import importlib
import subprocess
import logging
from typing import List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# List of required packages with their import names
REQUIRED_PACKAGES = [
    ("alembic", "alembic"),
    ("fastapi", "fastapi"),
    ("SQLAlchemy", "sqlalchemy"),
    ("uvicorn", "uvicorn"),
    ("requests", "requests"),
    ("beautifulsoup4", "bs4"),
    ("PyJWT", "jwt"),
    ("python-dotenv", "dotenv"),
    ("pydantic", "pydantic"),
    ("pandas", "pandas"),
    ("openai", "openai"),
    ("jinja2", "jinja2"),
    ("croniter", "croniter"),
    ("opentelemetry-api", "opentelemetry"),
    ("redis", "redis"),
    ("psycopg2-binary", "psycopg2"),
    ("httpx", "httpx"),
]

def check_package_availability() -> Tuple[List[str], List[str]]:
    """
    Check if all required packages are available.
    
    Returns:
        Tuple of (available_packages, missing_packages)
    """
    available = []
    missing = []
    
    for package_name, import_name in REQUIRED_PACKAGES:
        try:
            importlib.import_module(import_name)
            available.append(package_name)
            logger.debug(f"✓ {package_name} is available")
        except ImportError:
            missing.append(package_name)
            logger.warning(f"✗ {package_name} is missing")
    
    return available, missing

def main():
    """Main function to check dependencies."""
    logger.info("Checking SmartLinks Autopilot backend dependencies...")
    
    available, missing = check_package_availability()
    
    logger.info(f"Available packages: {len(available)}")
    if missing:
        logger.error(f"Missing packages: {len(missing)}")
        for package in missing:
            logger.error(f"  - {package}")
        
        # Try to install missing packages
        logger.info("Attempting to install missing packages...")
        for package in missing:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                logger.info(f"✓ Successfully installed {package}")
            except subprocess.CalledProcessError:
                logger.error(f"✗ Failed to install {package}")
                return 1
    else:
        logger.info("All required packages are available!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
