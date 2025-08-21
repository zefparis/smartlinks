#!/usr/bin/env python3
"""
Test script for the dynamic scraper factory system
"""

import sys
import os
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from soft.scraper.scraper_discovery import ScraperDiscovery
    from soft.scraper.scraper_runner import ScraperRunner
    print("✓ Successfully imported scraper modules")
except ImportError as e:
    print(f"✗ Failed to import scraper modules: {e}")
    sys.exit(1)

def test_scraper_discovery():
    """Test scraper discovery functionality"""
    print("\n=== Testing Scraper Discovery ===")
    
    try:
        discovery = ScraperDiscovery()
        scrapers = discovery.discover_scrapers()
        
        print(f"✓ Found {len(scrapers)} scrapers:")
        for scraper in scrapers:
            status_icon = "✓" if scraper["status"] == "available" else "⚠" if scraper["status"] == "missing_deps" else "✗"
            print(f"  {status_icon} {scraper['name']}: {scraper['status']}")
            if scraper.get("description"):
                print(f"    Description: {scraper['description'][:100]}...")
            print(f"    Entry point: {scraper['entry_point']}")
            if scraper.get("requirements"):
                print(f"    Requirements: {', '.join(scraper['requirements'][:3])}{'...' if len(scraper['requirements']) > 3 else ''}")
        
        return scrapers
        
    except Exception as e:
        print(f"✗ Scraper discovery failed: {e}")
        return []

async def test_scraper_runner():
    """Test scraper runner functionality"""
    print("\n=== Testing Scraper Runner ===")
    
    try:
        runner = ScraperRunner()
        
        # Test with a non-existent scraper
        print("Testing with non-existent scraper...")
        result = await runner.run_scraper("non-existent-scraper", {}, 30)
        
        if not result["success"]:
            print("✓ Correctly handled non-existent scraper")
        else:
            print("⚠ Unexpected success with non-existent scraper")
            
        return True
        
    except Exception as e:
        print(f"✗ Scraper runner test failed: {e}")
        return False

def test_external_scrapers_directory():
    """Test external_scrapers directory structure"""
    print("\n=== Testing External Scrapers Directory ===")
    
    external_scrapers_path = Path("external_scrapers")
    
    if not external_scrapers_path.exists():
        print("✗ external_scrapers directory not found")
        return False
    
    print(f"✓ external_scrapers directory exists: {external_scrapers_path.absolute()}")
    
    subdirs = [d for d in external_scrapers_path.iterdir() if d.is_dir()]
    print(f"✓ Found {len(subdirs)} subdirectories:")
    
    for subdir in subdirs:
        print(f"  📁 {subdir.name}")
        
        # Check for entry points
        entry_points = ["main.py", "scraper.py", "run.py", "__main__.py"]
        found_entry = None
        
        for entry in entry_points:
            if (subdir / entry).exists():
                found_entry = entry
                break
        
        if found_entry:
            print(f"    ✓ Entry point: {found_entry}")
        else:
            print(f"    ⚠ No entry point found (looking for: {', '.join(entry_points)})")
        
        # Check for requirements
        req_files = ["requirements.txt", "pyproject.toml"]
        for req_file in req_files:
            if (subdir / req_file).exists():
                print(f"    ✓ Requirements: {req_file}")
                break
        else:
            print(f"    ⚠ No requirements file found")
    
    return True

async def main():
    """Main test function"""
    print("🚀 Testing SmartLinks Autopilot Scraper Factory System")
    print("=" * 60)
    
    # Test external scrapers directory
    test_external_scrapers_directory()
    
    # Test scraper discovery
    scrapers = test_scraper_discovery()
    
    # Test scraper runner
    await test_scraper_runner()
    
    print("\n" + "=" * 60)
    print("🎯 Test Summary:")
    print(f"   • Scrapers discovered: {len(scrapers)}")
    print(f"   • Available scrapers: {len([s for s in scrapers if s['status'] == 'available'])}")
    print(f"   • Scrapers with missing deps: {len([s for s in scrapers if s['status'] == 'missing_deps'])}")
    print(f"   • Error scrapers: {len([s for s in scrapers if s['status'] == 'error'])}")
    
    if scrapers:
        print("\n✅ Scraper Factory System is functional!")
        print("   Ready for frontend integration and user testing.")
    else:
        print("\n⚠️  No scrapers found. Add Python scrapers to external_scrapers/ directory.")
    
    print("\n📝 Next steps:")
    print("   1. Start the backend server: python -m src.backend.main")
    print("   2. Start the frontend: cd src/frontend && npm run dev")
    print("   3. Navigate to /tools/scraper to test the UI")

if __name__ == "__main__":
    asyncio.run(main())
