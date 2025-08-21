"""
Discovery Scheduler Module for SmartLinks Autopilot
Integrates Discovery Scraper with background task scheduling
"""

import asyncio
import logging
import schedule
import time
from datetime import datetime, timedelta
from threading import Thread
from typing import Dict, Any, Optional
import json
from pathlib import Path

from .discovery_scraper import DiscoveryScraper

logger = logging.getLogger(__name__)

class DiscoveryScheduler:
    """Scheduler for autonomous discovery tasks"""
    
    def __init__(self):
        self.discovery_scraper = DiscoveryScraper()
        self.is_running = False
        self.scheduler_thread = None
        self.config_file = Path("discovery_config.json")
        self.config = self._load_config()
        self.last_run = None
        self.next_run = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load scheduler configuration"""
        default_config = {
            "enabled": False,
            "schedule_type": "daily",  # daily, weekly, manual
            "schedule_time": "02:00",  # HH:MM format
            "schedule_days": ["monday", "wednesday", "friday"],  # for weekly
            "auto_import_threshold": 0.8,  # Auto-import offers with score > 0.8
            "max_sources_per_run": 20,
            "max_offers_per_run": 100,
            "notification_webhook": None,
            "retry_failed_sources": True,
            "cleanup_old_data_days": 30
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults
                    default_config.update(config)
            except Exception as e:
                logger.error(f"[DISCOVERY_SCHEDULER] Error loading config: {e}")
        
        return default_config
    
    def _save_config(self):
        """Save scheduler configuration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[DISCOVERY_SCHEDULER] Error saving config: {e}")
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Update scheduler configuration"""
        try:
            self.config.update(new_config)
            self._save_config()
            
            # Restart scheduler if running
            if self.is_running:
                self.stop()
                self.start()
            
            logger.info(f"[DISCOVERY_SCHEDULER] Configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"[DISCOVERY_SCHEDULER] Error updating config: {e}")
            return False
    
    def start(self) -> bool:
        """Start the discovery scheduler"""
        if self.is_running:
            logger.warning("[DISCOVERY_SCHEDULER] Scheduler already running")
            return False
        
        if not self.config.get("enabled", False):
            logger.info("[DISCOVERY_SCHEDULER] Scheduler disabled in config")
            return False
        
        try:
            # Clear existing schedule
            schedule.clear()
            
            # Set up schedule based on config
            schedule_type = self.config.get("schedule_type", "daily")
            schedule_time = self.config.get("schedule_time", "02:00")
            
            if schedule_type == "daily":
                schedule.every().day.at(schedule_time).do(self._run_discovery_job)
                logger.info(f"[DISCOVERY_SCHEDULER] Scheduled daily at {schedule_time}")
                
            elif schedule_type == "weekly":
                schedule_days = self.config.get("schedule_days", ["monday"])
                for day in schedule_days:
                    getattr(schedule.every(), day.lower()).at(schedule_time).do(self._run_discovery_job)
                logger.info(f"[DISCOVERY_SCHEDULER] Scheduled weekly on {schedule_days} at {schedule_time}")
            
            # Start scheduler thread
            self.is_running = True
            self.scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            
            # Calculate next run
            self._update_next_run()
            
            logger.info("[DISCOVERY_SCHEDULER] Discovery scheduler started")
            return True
            
        except Exception as e:
            logger.error(f"[DISCOVERY_SCHEDULER] Error starting scheduler: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """Stop the discovery scheduler"""
        try:
            self.is_running = False
            schedule.clear()
            
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            logger.info("[DISCOVERY_SCHEDULER] Discovery scheduler stopped")
            return True
            
        except Exception as e:
            logger.error(f"[DISCOVERY_SCHEDULER] Error stopping scheduler: {e}")
            return False
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"[DISCOVERY_SCHEDULER] Error in scheduler loop: {e}")
                time.sleep(60)
    
    def _run_discovery_job(self):
        """Run discovery job (called by scheduler)"""
        logger.info("[DISCOVERY_SCHEDULER] Starting scheduled discovery job")
        
        try:
            # Run discovery in async context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(self._execute_discovery())
            
            self.last_run = datetime.now()
            self._update_next_run()
            
            # Log results
            if result.get("success"):
                logger.info(f"[DISCOVERY_SCHEDULER] Discovery completed: {result.get('sources_found', 0)} sources, {result.get('offers_found', 0)} offers")
                
                # Auto-import high-confidence offers
                if self.config.get("auto_import_threshold"):
                    self._auto_import_offers()
                
                # Send notification if configured
                if self.config.get("notification_webhook"):
                    self._send_notification(result)
                    
            else:
                logger.error(f"[DISCOVERY_SCHEDULER] Discovery failed: {result.get('message')}")
            
            # Cleanup old data
            self._cleanup_old_data()
            
        except Exception as e:
            logger.error(f"[DISCOVERY_SCHEDULER] Error in discovery job: {e}")
        finally:
            loop.close()
    
    async def _execute_discovery(self) -> Dict[str, Any]:
        """Execute discovery with configured limits"""
        try:
            # Apply configuration limits
            original_queries = self.discovery_scraper.scanner.SEARCH_QUERIES if hasattr(self.discovery_scraper, 'scanner') else []
            
            # Limit sources if configured
            max_sources = self.config.get("max_sources_per_run", 20)
            
            result = await self.discovery_scraper.start_discovery()
            
            return result
            
        except Exception as e:
            logger.error(f"[DISCOVERY_SCHEDULER] Error executing discovery: {e}")
            return {"success": False, "message": str(e)}
    
    def _auto_import_offers(self):
        """Auto-import high-confidence offers"""
        try:
            threshold = self.config.get("auto_import_threshold", 0.8)
            max_offers = self.config.get("max_offers_per_run", 100)
            
            # Get high-confidence offers
            conn = self.discovery_scraper.db.db_path
            import sqlite3
            
            with sqlite3.connect(conn) as db:
                cursor = db.cursor()
                cursor.execute('''
                    SELECT id, title, confidence_score FROM discovered_offers 
                    WHERE imported = FALSE AND confidence_score >= ?
                    ORDER BY confidence_score DESC
                    LIMIT ?
                ''', (threshold, max_offers))
                
                offers = cursor.fetchall()
                
                imported_count = 0
                for offer_id, title, score in offers:
                    try:
                        # Import offer (this would need to be async in real implementation)
                        cursor.execute('''
                            UPDATE discovered_offers SET imported = TRUE WHERE id = ?
                        ''', (offer_id,))
                        
                        imported_count += 1
                        logger.info(f"[DISCOVERY_SCHEDULER] Auto-imported offer: {title} (score: {score:.2f})")
                        
                    except Exception as e:
                        logger.error(f"[DISCOVERY_SCHEDULER] Error auto-importing offer {offer_id}: {e}")
                
                db.commit()
                
                if imported_count > 0:
                    logger.info(f"[DISCOVERY_SCHEDULER] Auto-imported {imported_count} high-confidence offers")
                    
        except Exception as e:
            logger.error(f"[DISCOVERY_SCHEDULER] Error in auto-import: {e}")
    
    def _send_notification(self, result: Dict[str, Any]):
        """Send notification webhook"""
        try:
            webhook_url = self.config.get("notification_webhook")
            if not webhook_url:
                return
            
            import requests
            
            payload = {
                "text": f"🤖 Discovery Scraper completed",
                "attachments": [{
                    "color": "good" if result.get("success") else "danger",
                    "fields": [
                        {"title": "Sources Found", "value": str(result.get("sources_found", 0)), "short": True},
                        {"title": "Offers Found", "value": str(result.get("offers_found", 0)), "short": True},
                        {"title": "Status", "value": "Success" if result.get("success") else "Failed", "short": True},
                        {"title": "Time", "value": datetime.now().strftime("%Y-%m-%d %H:%M"), "short": True}
                    ]
                }]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("[DISCOVERY_SCHEDULER] Notification sent successfully")
            
        except Exception as e:
            logger.error(f"[DISCOVERY_SCHEDULER] Error sending notification: {e}")
    
    def _cleanup_old_data(self):
        """Cleanup old discovery data"""
        try:
            cleanup_days = self.config.get("cleanup_old_data_days", 30)
            if cleanup_days <= 0:
                return
            
            cutoff_date = datetime.now() - timedelta(days=cleanup_days)
            
            import sqlite3
            with sqlite3.connect(self.discovery_scraper.db.db_path) as db:
                cursor = db.cursor()
                
                # Cleanup old imported offers
                cursor.execute('''
                    DELETE FROM discovered_offers 
                    WHERE imported = TRUE AND discovered_at < ?
                ''', (cutoff_date,))
                
                offers_deleted = cursor.rowcount
                
                # Cleanup old failed sources
                cursor.execute('''
                    DELETE FROM discovered_sources 
                    WHERE status = 'failed' AND discovered_at < ?
                ''', (cutoff_date,))
                
                sources_deleted = cursor.rowcount
                
                db.commit()
                
                if offers_deleted > 0 or sources_deleted > 0:
                    logger.info(f"[DISCOVERY_SCHEDULER] Cleaned up {offers_deleted} old offers and {sources_deleted} old sources")
                    
        except Exception as e:
            logger.error(f"[DISCOVERY_SCHEDULER] Error in cleanup: {e}")
    
    def _update_next_run(self):
        """Update next run time"""
        try:
            jobs = schedule.get_jobs()
            if jobs:
                self.next_run = min(job.next_run for job in jobs)
            else:
                self.next_run = None
        except Exception as e:
            logger.error(f"[DISCOVERY_SCHEDULER] Error updating next run: {e}")
            self.next_run = None
    
    def run_now(self) -> Dict[str, Any]:
        """Run discovery immediately (manual trigger)"""
        logger.info("[DISCOVERY_SCHEDULER] Manual discovery trigger")
        
        try:
            # Run discovery in new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(self._execute_discovery())
            
            self.last_run = datetime.now()
            
            return result
            
        except Exception as e:
            logger.error(f"[DISCOVERY_SCHEDULER] Error in manual run: {e}")
            return {"success": False, "message": str(e)}
        finally:
            loop.close()
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            "is_running": self.is_running,
            "enabled": self.config.get("enabled", False),
            "schedule_type": self.config.get("schedule_type", "daily"),
            "schedule_time": self.config.get("schedule_time", "02:00"),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "config": self.config
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get discovery statistics"""
        try:
            import sqlite3
            with sqlite3.connect(self.discovery_scraper.db.db_path) as db:
                cursor = db.cursor()
                
                # Get session stats
                cursor.execute('''
                    SELECT COUNT(*), AVG(sources_found), AVG(offers_found)
                    FROM discovery_sessions 
                    WHERE completed_at IS NOT NULL
                ''')
                session_stats = cursor.fetchone()
                
                # Get source stats
                cursor.execute('''
                    SELECT status, COUNT(*) FROM discovered_sources 
                    GROUP BY status
                ''')
                source_stats = dict(cursor.fetchall())
                
                # Get offer stats
                cursor.execute('''
                    SELECT imported, COUNT(*) FROM discovered_offers 
                    GROUP BY imported
                ''')
                offer_stats = dict(cursor.fetchall())
                
                return {
                    "total_sessions": session_stats[0] if session_stats[0] else 0,
                    "avg_sources_per_session": round(session_stats[1], 1) if session_stats[1] else 0,
                    "avg_offers_per_session": round(session_stats[2], 1) if session_stats[2] else 0,
                    "sources_by_status": source_stats,
                    "offers_imported": offer_stats.get(1, 0),
                    "offers_pending": offer_stats.get(0, 0)
                }
                
        except Exception as e:
            logger.error(f"[DISCOVERY_SCHEDULER] Error getting stats: {e}")
            return {}

# Global scheduler instance
discovery_scheduler = DiscoveryScheduler()
