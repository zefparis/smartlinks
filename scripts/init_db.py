#!/usr/bin/env python3
"""
Script to initialize the database and run migrations.
"""
import os
import sys
import logging
from alembic.config import Config
from alembic import command

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """Run database migrations using Alembic."""
    try:
        # Get the directory containing this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to the project root
        project_root = os.path.dirname(script_dir)
        
        # Set up Alembic config
        alembic_cfg = Config(os.path.join(project_root, "alembic.ini"))
        
        # Set the script location to the migrations directory
        migrations_dir = os.path.join(project_root, "migrations")
        alembic_cfg.set_main_option('script_location', migrations_dir)
        
        # Run migrations
        logger.info("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations completed successfully!")
        
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        sys.exit(1)

def main():
    """Main function to initialize the database."""
    try:
        # Import the init_db function from the main package
        from src.soft.initdb import main as init_db_main
        
        # Run migrations first
        run_migrations()
        
        # Then run the init_db script to seed initial data
        logger.info("Seeding initial data...")
        init_db_main()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
