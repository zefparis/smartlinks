#!/usr/bin/env python3
"""Diagnostic and fix script for SmartLinks Autopilot RCP setup."""

import sys
import os
import subprocess
import importlib.util

def check_dependency(package_name, import_name=None):
    """Check if a dependency is installed and can be imported."""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✅ {package_name}: OK")
        return True
    except ImportError:
        print(f"❌ {package_name}: Missing")
        return False

def install_package(package_name):
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ Installed {package_name}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package_name}")
        return False

def main():
    """Main diagnostic and fix routine."""
    print("SmartLinks Autopilot RCP - Diagnostic & Fix\n")
    
    # Check critical dependencies
    critical_deps = [
        ("aiohttp", "aiohttp"),
        ("redis", "redis"),
        ("ortools", "ortools"),
        ("opentelemetry-api", "opentelemetry"),
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("PyYAML", "yaml")
    ]
    
    missing_deps = []
    
    print("Checking dependencies...")
    for package, import_name in critical_deps:
        if not check_dependency(package, import_name):
            missing_deps.append(package)
    
    # Install missing dependencies
    if missing_deps:
        print(f"\nInstalling {len(missing_deps)} missing dependencies...")
        for package in missing_deps:
            install_package(package)
    else:
        print("\n✅ All critical dependencies are installed!")
    
    # Check if we can import our new modules
    print("\nChecking RCP modules...")
    
    # Create __init__.py files if missing
    init_files = [
        "src/__init__.py",
        "src/soft/__init__.py",
        "src/soft/pac/__init__.py",
        "src/soft/replay/__init__.py",
        "src/soft/features/__init__.py",
        "src/soft/bandits/__init__.py",
        "src/soft/optimizer/__init__.py",
        "src/soft/backtesting/__init__.py",
        "src/soft/webhooks/__init__.py",
        "src/soft/observability/__init__.py",
        "src/soft/autopilot/__init__.py",
        "src/soft/autopilot/bandits/__init__.py",
        "src/soft/autopilot/planner/__init__.py"
    ]
    
    for init_file in init_files:
        if not os.path.exists(init_file):
            os.makedirs(os.path.dirname(init_file), exist_ok=True)
            with open(init_file, 'w') as f:
                f.write('"""Package initialization."""\n')
            print(f"Created {init_file}")
    
    # Test basic server startup
    print("\nTesting basic server import...")
    try:
        sys.path.insert(0, os.getcwd())
        from src.soft.router import app
        print("✅ Server can be imported successfully!")
        
        # Test new API routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and route.path.startswith('/api/'):
                routes.append(route.path)
        
        new_routes = [r for r in routes if any(x in r for x in ['pac', 'replay', 'features', 'bandits', 'optimizer', 'backtest', 'webhooks'])]
        
        if new_routes:
            print(f"✅ Found {len(new_routes)} new RCP API routes:")
            for route in sorted(new_routes)[:10]:  # Show first 10
                print(f"  - {route}")
        else:
            print("⚠️  No new RCP routes found")
            
    except Exception as e:
        print(f"❌ Server import failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nDiagnostic complete!")

if __name__ == "__main__":
    main()
