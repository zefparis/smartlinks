#!/usr/bin/env python3
"""Script to run Alembic migrations for SmartLinks Autopilot."""

import os
import sys
from alembic.config import Config
from alembic import command

def run_migrations():
    """Run Alembic migrations to upgrade database to head."""
    try:
        # Get the directory containing this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Path to alembic.ini
        alembic_cfg_path = os.path.join(script_dir, "alembic.ini")
        
        if not os.path.exists(alembic_cfg_path):
            print(f"❌ alembic.ini not found at {alembic_cfg_path}")
            return False
        
        print("🔄 Running Alembic migrations...")
        
        # Create Alembic configuration
        alembic_cfg = Config(alembic_cfg_path)
        
        # Run upgrade to head
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Database migrations completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
