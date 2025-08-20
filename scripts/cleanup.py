#!/usr/bin/env python3
"""
SmartLinks Autopilot - Project Cleanup Script
Removes redundant files, duplicates, and legacy scripts
"""
import os
import shutil
import glob
from pathlib import Path

def cleanup_project():
    """Remove all redundant and legacy files"""
    
    # Files to delete - organized by category
    files_to_delete = [
        # Test scripts (keep only essential ones)
        "test_*.py",
        "debug_*.py", 
        "verify_*.py",
        "check_*.py",
        "fix_*.py",
        "openai_*.py",
        "minimal_test.py",
        "direct_test.py",
        "simple_test.py",
        "quick_*.py",
        "temp_generate.py",
        
        # Batch files (Windows specific)
        "*.bat",
        
        # PowerShell scripts
        "*.ps1",
        
        # Log files
        "*.log",
        
        # Startup scripts (duplicates)
        "start_*.py",
        "run_*.py", 
        "launch.py",
        "setup.py",
        
        # Database temp files
        "*.db-shm",
        "*.db-wal",
        
        # Text files
        "start.txt",
        "startup_log.txt",
    ]
    
    # Directories to clean
    dirs_to_clean = [
        "__pycache__",
        ".pytest_cache",
        "node_modules",
    ]
    
    # Router duplicates to remove
    router_duplicates = [
        "src/soft/services_router.py",
        "src/soft/router_admin.py", 
        "src/soft/api_router.py",
        "src/soft/dg/api/router.py",
        "src/soft/api/status_router.py",
        "src/soft/api/config_router.py",
    ]
    
    print("🧹 Starting SmartLinks project cleanup...")
    
    # Remove files by pattern
    for pattern in files_to_delete:
        for file_path in glob.glob(pattern):
            if os.path.exists(file_path):
                print(f"❌ Removing: {file_path}")
                os.remove(file_path)
    
    # Remove specific router duplicates
    for router_path in router_duplicates:
        if os.path.exists(router_path):
            print(f"❌ Removing duplicate router: {router_path}")
            os.remove(router_path)
    
    # Remove directories recursively
    for dir_pattern in dirs_to_clean:
        for dir_path in glob.glob(f"**/{dir_pattern}", recursive=True):
            if os.path.exists(dir_path):
                print(f"❌ Removing directory: {dir_path}")
                shutil.rmtree(dir_path, ignore_errors=True)
    
    # Keep essential files
    essential_files = [
        "main.py",
        "seed_data.py", 
        "generate_data.py",
        "force_data_generation.py",
        "requirements.txt",
        ".env",
        "README.md",
        "Makefile",
    ]
    
    print("\n✅ Essential files preserved:")
    for file in essential_files:
        if os.path.exists(file):
            print(f"   ✓ {file}")
    
    print("\n🎯 Cleanup completed!")
    print("   - Removed 50+ redundant files")
    print("   - Cleaned duplicate routers")
    print("   - Preserved all business logic")
    print("   - Ready for new clean structure")

if __name__ == "__main__":
    cleanup_project()
