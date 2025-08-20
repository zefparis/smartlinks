#!/usr/bin/env python3
"""Quick setup script for SmartLinks Autopilot RCP."""

import os
import sys
import subprocess

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - Failed")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False

def test_imports():
    """Test importing RCP modules."""
    print("🔄 Testing RCP module imports...")
    
    modules_to_test = [
        ("src.soft.pac.schemas", "Policy-as-Code schemas"),
        ("src.soft.rcp.api", "RCP API router"),
        ("src.soft.autopilot.bandits.thompson", "Bandits algorithms"),
        ("src.soft.webhooks.service", "Webhooks service"),
    ]
    
    success_count = 0
    for module, description in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {description}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {description} - Import error: {e}")
        except Exception as e:
            print(f"❌ {description} - Error: {e}")
    
    print(f"\nImport results: {success_count}/{len(modules_to_test)} modules OK")
    return success_count == len(modules_to_test)

def run_migrations():
    """Run Alembic migrations."""
    print("🔄 Running database migrations...")
    try:
        from alembic.config import Config
        from alembic import command
        
        if not os.path.exists("alembic.ini"):
            print("❌ alembic.ini not found")
            return False
        
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("✅ Database migrations completed")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    """Main setup routine."""
    print("SmartLinks Autopilot RCP - Quick Setup\n")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Test basic dependencies
    deps_ok = run_command("python -c \"import fastapi, sqlalchemy, redis; print('Core deps OK')\"", 
                         "Testing core dependencies")
    
    # Test imports
    imports_ok = test_imports()
    
    # Run migrations
    migrations_ok = run_migrations()
    
    # Test server import
    server_ok = run_command("python -c \"from src.soft.router import app; print('Server import OK')\"",
                           "Testing server import")
    
    print(f"\n📊 Setup Summary:")
    print(f"   Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"   RCP Imports:  {'✅' if imports_ok else '❌'}")
    print(f"   Migrations:   {'✅' if migrations_ok else '❌'}")
    print(f"   Server:       {'✅' if server_ok else '❌'}")
    
    if all([deps_ok, imports_ok, migrations_ok, server_ok]):
        print("\n🎉 RCP system is ready!")
        print("\nNext steps:")
        print("1. Start server: python start_debug.py")
        print("2. Open API docs: http://localhost:8000/docs")
        print("3. Test RCP endpoints with X-Role header")
    else:
        print("\n⚠️  Some components need attention")
        print("\nTroubleshooting:")
        print("- Install missing deps: pip install -r requirements.txt")
        print("- Check alembic.ini exists")
        print("- Verify __init__.py files in all packages")

if __name__ == "__main__":
    main()
