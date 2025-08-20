#!/usr/bin/env python3
"""Direct database migration script."""

import os
import sys

def migrate_database():
    """Run database migrations directly."""
    try:
        # Import Alembic
        from alembic.config import Config
        from alembic import command
        
        print("Running database migrations...")
        
        # Check if alembic.ini exists
        if not os.path.exists("alembic.ini"):
            print("❌ alembic.ini not found")
            return False
        
        # Create Alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Run upgrade to head
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Database migrations completed successfully!")
        return True
        
    except ImportError:
        print("❌ Alembic not installed. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "alembic"])
        return migrate_database()  # Retry after installation
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("\n🎉 Ready to start server!")
        print("Run: python start_debug.py")
    else:
        print("\n⚠️ Migration failed. Check database configuration.")
