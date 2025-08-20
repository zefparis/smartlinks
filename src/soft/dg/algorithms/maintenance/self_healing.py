"""
Self-Healing Module for SmartLinks Autonomous DG.

This module detects and automatically fixes common issues in the system,
including performance degradation, failed API calls, and configuration problems.
"""
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import random

from ...models.decision import Action, DecisionContext
from ..base import Algorithm, AlgorithmResult

logger = logging.getLogger(__name__)

class SelfHealingAlgorithm(Algorithm):
    """Algorithm for automatic issue detection and resolution."""
    
    # Default configuration
    DEFAULT_CONFIG = {
        "health_checks": {
            "api_errors": {
                "enabled": True,
                "threshold": 5,  # Number of errors before taking action
                "time_window_minutes": 15,
                "actions": ["retry", "degrade", "alert"]
            },
            "high_latency": {
                "enabled": True,
                "threshold_ms": 1000,  # Response time threshold in ms
                "sample_rate": 0.1,    # Percentage of requests to monitor
                "actions": ["cache_more", "scale_up", "alert"]
            },
            "resource_usage": {
                "enabled": True,
                "cpu_threshold": 90,    # Percentage
                "memory_threshold": 90,  # Percentage
                "disk_threshold": 90,    # Percentage
                "actions": ["scale_up", "cleanup", "alert"]
            },
            "data_integrity": {
                "enabled": True,
                "check_interval_minutes": 60,
                "actions": ["repair", "alert"]
            }
        },
        "action_priorities": {
            "retry": 50,
            "degrade": 70,
            "alert": 90,
            "cache_more": 60,
            "scale_up": 80,
            "cleanup": 40,
            "repair": 100
        },
        "max_concurrent_repairs": 3,
        "cooldown_period_minutes": 5,
        "blacklist_duration_minutes": 60
    }
    
    @classmethod
    def get_name(cls) -> str:
        return "self_healing"
    
    def __init__(self):
        self.issue_history = {}
        self.last_check = {}
        self.active_repairs = {}
    
    async def execute(self, context: DecisionContext, 
                     config: Optional[Dict[str, Any]] = None) -> AlgorithmResult:
        """Execute the self-healing algorithm.
        
        Args:
            context: Current decision context
            config: Algorithm configuration (overrides defaults)
            
        Returns:
            AlgorithmResult containing healing actions and diagnostics
        """
        # Merge default config with provided config
        config = {**self.DEFAULT_CONFIG, **(config or {})}
        
        try:
            # Initialize result variables
            actions = []
            diagnostics = {
                "checks_performed": 0,
                "issues_found": 0,
                "actions_taken": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Get system metrics from context
            metrics = context.metrics or {}
            system_metrics = metrics.get("system", {})
            api_metrics = metrics.get("api", {})
            
            # Run enabled health checks
            for check_name, check_config in config["health_checks"].items():
                if not check_config.get("enabled", True):
                    continue
                    
                diagnostics["checks_performed"] += 1
                
                # Check if we're in cooldown for this check
                if self._is_in_cooldown(check_name, config):
                    continue
                
                # Run the appropriate check
                check_method = getattr(self, f"_check_{check_name}", None)
                if not check_method or not callable(check_method):
                    logger.warning(f"No check method for: {check_name}")
                    continue
                
                # Execute the check
                issue_found, check_actions = await check_method(
                    context, 
                    {**check_config, **check_config.get("params", {})}, 
                    config
                )
                
                if issue_found:
                    diagnostics["issues_found"] += 1
                    
                    # Filter and prioritize actions
                    valid_actions = [
                        a for a in check_actions 
                        if a.action_type in config["action_priorities"]
                    ]
                    
                    # Sort by priority (highest first)
                    valid_actions.sort(
                        key=lambda a: config["action_priorities"].get(a.action_type, 0),
                        reverse=True
                    )
                    
                    # Add actions to result
                    for action in valid_actions:
                        # Skip if we've reached max concurrent repairs
                        if action.action_type == "repair":
                            if len(self.active_repairs) >= config["max_concurrent_repairs"]:
                                logger.warning("Max concurrent repairs reached, skipping repair action")
                                continue
                            
                            # Track active repairs
                            repair_id = f"{check_name}_{int(time.time())}"
                            self.active_repairs[repair_id] = {
                                "started_at": datetime.utcnow(),
                                "check": check_name,
                                "action": action
                            }
                            
                            # Add repair ID to action params
                            action.params["repair_id"] = repair_id
                        
                        actions.append(action)
                        diagnostics["actions_taken"] += 1
                        
                        # Update last check time
                        self.last_check[check_name] = datetime.utcnow()
                        
                        # If this is a high-priority action, don't continue with other checks
                        if config["action_priorities"].get(action.action_type, 0) >= 80:
                            break
            
            # Clean up completed repairs
            self._cleanup_completed_repairs()
            
            # Calculate confidence based on actions taken
            confidence = 0.7  # Base confidence
            if diagnostics["issues_found"] > 0:
                # Higher confidence when we find and fix issues
                confidence = min(0.9, confidence + (0.1 * diagnostics["actions_taken"]))
            
            return AlgorithmResult(
                algorithm_name=self.get_name(),
                confidence=confidence,
                recommended_actions=actions,
                metadata={
                    **diagnostics,
                    "active_repairs": len(self.active_repairs),
                    "checks": list(config["health_checks"].keys())
                }
            )
            
        except Exception as e:
            logger.error(f"Error in self-healing module: {e}", exc_info=True)
            return AlgorithmResult(
                algorithm_name=self.get_name(),
                confidence=0.0,
                recommended_actions=[],
                metadata={
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    def _is_in_cooldown(self, check_name: str, config: Dict[str, Any]) -> bool:
        """Check if a health check is in cooldown period."""
        if check_name not in self.last_check:
            return False
            
        cooldown = timedelta(minutes=config.get("cooldown_period_minutes", 5))
        return (datetime.utcnow() - self.last_check[check_name]) < cooldown
    
    def _cleanup_completed_repairs(self) -> None:
        """Remove completed or stale repairs from tracking."""
        now = datetime.utcnow()
        stale_repairs = []
        
        for repair_id, repair in list(self.active_repairs.items()):
            # Consider repairs older than 1 hour as stale
            if (now - repair["started_at"]) > timedelta(hours=1):
                stale_repairs.append(repair_id)
        
        # Remove stale repairs
        for repair_id in stale_repairs:
            logger.warning(f"Removing stale repair: {repair_id}")
            self.active_repairs.pop(repair_id, None)
    
    async def _check_api_errors(self, context: DecisionContext, 
                              check_config: Dict[str, Any],
                              global_config: Dict[str, Any]) -> Tuple[bool, List[Action]]:
        """Check for excessive API errors."""
        api_metrics = (context.metrics or {}).get("api", {})
        error_count = api_metrics.get("error_count", 0)
        total_requests = api_metrics.get("total_requests", 1)  # Avoid division by zero
        error_rate = (error_count / total_requests) * 100
        
        threshold = check_config.get("threshold", 5)
        time_window = check_config.get("time_window_minutes", 15)
        
        issue_detected = error_count >= threshold
        actions = []
        
        if issue_detected:
            logger.warning(
                f"High API error rate detected: {error_count} errors "
                f"({error_rate:.1f}%) in last {time_window} minutes"
            )
            
            # Generate appropriate actions based on configuration
            for action_type in check_config.get("actions", []):
                if action_type == "retry":
                    actions.append(Action(
                        action_type="retry_failed_requests",
                        params={
                            "error_count": error_count,
                            "error_rate": error_rate,
                            "time_window_minutes": time_window
                        },
                        priority=global_config["action_priorities"].get("retry", 50),
                        description=f"Retry {error_count} failed API requests from the last {time_window} minutes",
                        source_algorithm=self.get_name()
                    ))
                
                elif action_type == "degrade":
                    actions.append(Action(
                        action_type="degrade_service",
                        params={
                            "service": "api",
                            "level": "reduced",
                            "reason": f"High error rate: {error_rate:.1f}%"
                        },
                        priority=global_config["action_priorities"].get("degrade", 70),
                        description="Degrade API service to reduce error impact",
                        source_algorithm=self.get_name()
                    ))
                
                elif action_type == "alert":
                    actions.append(Action(
                        action_type="create_alert",
                        params={
                            "level": "warning",
                            "title": "High API Error Rate",
                            "message": (
                                f"Detected {error_count} API errors ({error_rate:.1f}%) "
                                f"in the last {time_window} minutes"
                            ),
                            "metrics": {
                                "error_count": error_count,
                                "total_requests": total_requests,
                                "error_rate": error_rate
                            }
                        },
                        priority=global_config["action_priorities"].get("alert", 90),
                        description="Alert team about high API error rate",
                        source_algorithm=self.get_name()
                    ))
        
        return issue_detected, actions
    
    async def _check_high_latency(self, context: DecisionContext, 
                                check_config: Dict[str, Any],
                                global_config: Dict[str, Any]) -> Tuple[bool, List[Action]]:
        """Check for high latency in API responses."""
        api_metrics = (context.metrics or {}).get("api", {})
        avg_latency = api_metrics.get("avg_latency_ms", 0)
        threshold = check_config.get("threshold_ms", 1000)
        
        issue_detected = avg_latency > threshold
        actions = []
        
        if issue_detected:
            logger.warning(
                f"High API latency detected: {avg_latency:.1f}ms "
                f"(threshold: {threshold}ms)"
            )
            
            # Generate appropriate actions
            for action_type in check_config.get("actions", []):
                if action_type == "cache_more":
                    actions.append(Action(
                        action_type="increase_cache_ttl",
                        params={
                            "current_ttl": api_metrics.get("cache_ttl_seconds", 300),
                            "new_ttl": 1800,  # 30 minutes
                            "reason": f"High API latency: {avg_latency:.1f}ms"
                        },
                        priority=global_config["action_priorities"].get("cache_more", 60),
                        description="Increase cache TTL to reduce API load",
                        source_algorithm=self.get_name()
                    ))
                
                elif action_type == "scale_up":
                    actions.append(Action(
                        action_type="scale_service",
                        params={
                            "service": "api",
                            "direction": "up",
                            "reason": f"High API latency: {avg_latency:.1f}ms"
                        },
                        priority=global_config["action_priorities"].get("scale_up", 80),
                        description="Scale up API service to handle increased load",
                        source_algorithm=self.get_name()
                    ))
                
                elif action_type == "alert":
                    actions.append(Action(
                        action_type="create_alert",
                        params={
                            "level": "warning",
                            "title": "High API Latency",
                            "message": (
                                f"High API latency detected: {avg_latency:.1f}ms "
                                f"(threshold: {threshold}ms)"
                            ),
                            "metrics": {
                                "avg_latency_ms": avg_latency,
                                "threshold_ms": threshold,
                                "sample_size": api_metrics.get("request_count", 0)
                            }
                        },
                        priority=global_config["action_priorities"].get("alert", 90),
                        description="Alert team about high API latency",
                        source_algorithm=self.get_name()
                    ))
        
        return issue_detected, actions
    
    async def _check_resource_usage(self, context: DecisionContext, 
                                  check_config: Dict[str, Any],
                                  global_config: Dict[str, Any]) -> Tuple[bool, List[Action]]:
        """Check for high resource usage (CPU, memory, disk)."""
        system_metrics = (context.metrics or {}).get("system", {})
        
        # Check CPU usage
        cpu_usage = system_metrics.get("cpu_percent", 0)
        cpu_threshold = check_config.get("cpu_threshold", 90)
        cpu_high = cpu_usage > cpu_threshold
        
        # Check memory usage
        mem_usage = system_metrics.get("memory_percent", 0)
        mem_threshold = check_config.get("memory_threshold", 90)
        mem_high = mem_usage > mem_threshold
        
        # Check disk usage
        disk_usage = system_metrics.get("disk_percent", 0)
        disk_threshold = check_config.get("disk_threshold", 90)
        disk_high = disk_usage > disk_threshold
        
        issue_detected = cpu_high or mem_high or disk_high
        actions = []
        
        if issue_detected:
            logger.warning(
                f"High resource usage detected - CPU: {cpu_usage}% (>{cpu_threshold}%), "
                f"Memory: {mem_usage}% (>{mem_threshold}%), "
                f"Disk: {disk_usage}% (>{disk_threshold}%)"
            )
            
            # Generate appropriate actions
            for action_type in check_config.get("actions", []):
                if action_type == "scale_up" and (cpu_high or mem_high):
                    # Only scale up if CPU or memory is high, not for disk
                    actions.append(Action(
                        action_type="scale_service",
                        params={
                            "service": "all",
                            "direction": "up",
                            "reason": (
                                f"High resource usage - CPU: {cpu_usage}%, "
                                f"Memory: {mem_usage}%"
                            )
                        },
                        priority=global_config["action_priorities"].get("scale_up", 80),
                        description="Scale up services to handle increased load",
                        source_algorithm=self.get_name()
                    ))
                
                elif action_type == "cleanup":
                    # Clean up temporary files, caches, etc.
                    if disk_high:
                        actions.append(Action(
                            action_type="cleanup_disk",
                            params={
                                "target": "temporary_files",
                                "max_age_days": 1,
                                "reason": f"High disk usage: {disk_usage}%"
                            },
                            priority=global_config["action_priorities"].get("cleanup", 40),
                            description="Clean up temporary files to free disk space",
                            source_algorithm=self.get_name()
                        ))
                    
                    if mem_high:
                        actions.append(Action(
                            action_type="clear_cache",
                            params={
                                "cache_type": "in_memory",
                                "reason": f"High memory usage: {mem_usage}%"
                            },
                            priority=global_config["action_priorities"].get("cleanup", 40),
                            description="Clear in-memory caches to reduce memory pressure",
                            source_algorithm=self.get_name()
                        ))
                
                elif action_type == "alert":
                    # Generate alert with resource usage details
                    alert_params = {
                        "level": "warning",
                        "title": "High Resource Usage",
                        "message": (
                            "High resource usage detected:\n"
                            f"- CPU: {cpu_usage}% (threshold: {cpu_threshold}%)\n"
                            f"- Memory: {mem_usage}% (threshold: {mem_threshold}%)\n"
                            f"- Disk: {disk_usage}% (threshold: {disk_threshold}%)"
                        ),
                        "metrics": {
                            "cpu_percent": cpu_usage,
                            "memory_percent": mem_usage,
                            "disk_percent": disk_usage
                        }
                    }
                    
                    # Increase alert level if multiple resources are affected
                    if (cpu_high and mem_high) or (cpu_high and disk_high) or (mem_high and disk_high):
                        alert_params["level"] = "critical"
                    
                    actions.append(Action(
                        action_type="create_alert",
                        params=alert_params,
                        priority=global_config["action_priorities"].get("alert", 90),
                        description="Alert team about high resource usage",
                        source_algorithm=self.get_name()
                    ))
        
        return issue_detected, actions
    
    async def _check_data_integrity(self, context: DecisionContext, 
                                  check_config: Dict[str, Any],
                                  global_config: Dict[str, Any]) -> Tuple[bool, List[Action]]:
        """Check for data integrity issues in the system."""
        # In a real implementation, this would check for:
        # - Orphaned records
        # - Referential integrity issues
        # - Data consistency problems
        # - Stale or outdated data
        
        # For now, we'll simulate occasional data integrity issues
        issue_detected = random.random() < 0.1  # 10% chance of finding an issue
        actions = []
        
        if issue_detected:
            # Simulate different types of data integrity issues
            issue_type = random.choice([
                "orphaned_records",
                "referential_integrity",
                "data_consistency",
                "stale_data"
            ])
            
            logger.warning(f"Data integrity issue detected: {issue_type}")
            
            # Generate appropriate actions
            for action_type in check_config.get("actions", []):
                if action_type == "repair":
                    actions.append(Action(
                        action_type="repair_data_integrity",
                        params={
                            "issue_type": issue_type,
                            "scope": "automated",
                            "backup_first": True
                        },
                        priority=global_config["action_priorities"].get("repair", 100),
                        description=f"Repair {issue_type.replace('_', ' ')} issue",
                        source_algorithm=self.get_name()
                    ))
                
                elif action_type == "alert":
                    actions.append(Action(
                        action_type="create_alert",
                        params={
                            "level": "error",
                            "title": f"Data Integrity Issue: {issue_type.replace('_', ' ').title()}",
                            "message": f"Detected {issue_type.replace('_', ' ')} issue that may require attention.",
                            "metadata": {
                                "issue_type": issue_type,
                                "detected_at": datetime.utcnow().isoformat(),
                                "severity": "high"
                            }
                        },
                        priority=global_config["action_priorities"].get("alert", 90),
                        description=f"Alert team about {issue_type} issue",
                        source_algorithm=self.get_name()
                    ))
        
        return issue_detected, actions
