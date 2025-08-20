#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SmartLinks Autopilot - Repository Cleanup & Migration Script
Migrates to clean architecture with dry-run capability
"""
import os
import json
import shutil
import glob
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import argparse

class RepoCleanup:
    def __init__(self, dry_run: bool = True, backup: bool = True):
        self.dry_run = dry_run
        self.backup = backup
        self.backup_dir = None
        self.deleted_files = []
        self.moved_files = []
        self.errors = []
        
        if backup and not dry_run:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_dir = Path(f"./backup_{timestamp}")
            self.backup_dir.mkdir(exist_ok=True)
    
    def load_cleanup_plan(self) -> Dict[str, Any]:
        """Load cleanup plan from JSON"""
        plan_file = Path("scripts/cleanup_plan.json")
        if not plan_file.exists():
            raise FileNotFoundError("cleanup_plan.json not found in scripts/")
        
        with open(plan_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def expand_patterns(self, patterns: List[str]) -> List[Path]:
        """Expand glob patterns to actual file paths"""
        files = []
        for pattern in patterns:
            if '*' in pattern:
                matches = glob.glob(pattern, recursive=True)
                files.extend([Path(f) for f in matches if Path(f).is_file()])
            else:
                file_path = Path(pattern)
                if file_path.exists() and file_path.is_file():
                    files.append(file_path)
        return files
    
    def backup_file(self, file_path: Path) -> None:
        """Backup file before deletion"""
        if not self.backup_dir:
            return
        
        try:
            # Preserve directory structure in backup
            relative_path = file_path.relative_to(Path.cwd())
            backup_path = self.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
        except Exception as e:
            self.errors.append(f"Failed to backup {file_path}: {e}")
    
    def delete_files(self, file_patterns: List[str], category: str) -> None:
        """Delete files matching patterns"""
        files_to_delete = self.expand_patterns(file_patterns)
        
        print(f"\n🗑️  {category.upper()}:")
        if not files_to_delete:
            print("   No files found matching patterns")
            return
        
        for file_path in files_to_delete:
            try:
                if self.dry_run:
                    print(f"   [DRY-RUN] Would delete: {file_path}")
                else:
                    if self.backup:
                        self.backup_file(file_path)
                    file_path.unlink()
                    print(f"   ❌ Deleted: {file_path}")
                    self.deleted_files.append(str(file_path))
            except Exception as e:
                error_msg = f"Failed to delete {file_path}: {e}"
                self.errors.append(error_msg)
                print(f"   ⚠️  {error_msg}")
    
    def merge_routers(self, source: str, target: str) -> None:
        """Merge router files (placeholder for manual merge)"""
        source_path = Path(source)
        target_path = Path(target.replace("merge_into:", ""))
        
        if self.dry_run:
            print(f"   [DRY-RUN] Would merge {source_path} into {target_path}")
        else:
            print(f"   ⚠️  MANUAL ACTION REQUIRED: Merge {source_path} into {target_path}")
            print(f"       Then delete {source_path}")
    
    def run_cleanup(self) -> None:
        """Execute the cleanup process"""
        print("🧹 SMARTLINKS AUTOPILOT - REPOSITORY CLEANUP")
        print("=" * 60)
        
        if self.dry_run:
            print("🔍 DRY-RUN MODE - No files will be deleted")
        else:
            print("⚠️  LIVE MODE - Files will be permanently deleted")
            if self.backup:
                print(f"📦 Backup directory: {self.backup_dir}")
        
        print()
        
        try:
            plan = self.load_cleanup_plan()
            
            # Delete duplicate routers
            self.delete_files(
                plan["files_to_delete"]["duplicate_routers"],
                "Duplicate Routers"
            )
            
            # Delete legacy test scripts
            self.delete_files(
                plan["files_to_delete"]["legacy_test_scripts"],
                "Legacy Test Scripts"
            )
            
            # Delete Windows batch files
            self.delete_files(
                plan["files_to_delete"]["windows_batch_files"],
                "Windows Batch Files"
            )
            
            # Delete log files
            self.delete_files(
                plan["files_to_delete"]["log_files"],
                "Log Files"
            )
            
            # Delete startup script duplicates
            self.delete_files(
                plan["files_to_delete"]["startup_scripts_duplicates"],
                "Startup Script Duplicates"
            )
            
            # Delete database temp files
            self.delete_files(
                plan["files_to_delete"]["database_temp_files"],
                "Database Temp Files"
            )
            
            # Delete misc temp files
            self.delete_files(
                plan["files_to_delete"]["misc_temp_files"],
                "Misc Temp Files"
            )
            
            # Handle router merges
            print("\n🔄 ROUTER CONSOLIDATION:")
            for source, target in plan["files_to_move"]["consolidate_routers"].items():
                self.merge_routers(source, target)
            
            # Summary
            print("\n📊 CLEANUP SUMMARY:")
            print("-" * 30)
            if self.dry_run:
                print("   Mode: DRY-RUN (no changes made)")
            else:
                print(f"   Files deleted: {len(self.deleted_files)}")
                print(f"   Files moved: {len(self.moved_files)}")
                if self.backup_dir:
                    print(f"   Backup location: {self.backup_dir}")
            
            if self.errors:
                print(f"   Errors: {len(self.errors)}")
                for error in self.errors:
                    print(f"     - {error}")
            
            print("\n✅ Next steps:")
            print("   1. Fix critical backend/frontend issues")
            print("   2. Run validation tests")
            print("   3. Verify all endpoints work")
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return False
        
        return True

def main():
    parser = argparse.ArgumentParser(description="SmartLinks Autopilot Repository Cleanup")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")
    
    args = parser.parse_args()
    
    cleanup = RepoCleanup(
        dry_run=not args.apply,
        backup=not args.no_backup
    )
    
    success = cleanup.run_cleanup()
    
    if not success:
        exit(1)
    
    if cleanup.dry_run:
        print("\n🚀 To apply changes, run: python scripts/cleanup_repo.py --apply")

if __name__ == "__main__":
    main()
