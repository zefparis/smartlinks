"""
Predictive Alerting System for SmartLinks Autonomous DG.

This module detects potential issues before they become critical by analyzing
trends and patterns in system metrics.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from ...models.decision import Action, DecisionContext
from ..base import Algorithm, AlgorithmResult

logger = logging.getLogger(__name__)

class PredictiveAlerting(Algorithm):
    """Algorithm for predictive alerting and anomaly detection."""
    
    # Default configuration
    DEFAULT_CONFIG = {
        "metrics_to_monitor": [
            "response_time_p99",
            "error_rate",
            "cpu_usage",
            "memory_usage",
            "request_throughput"
        ],
        "thresholds": {
            "response_time_p99": {"warning": 1000, "critical": 2000},  # ms
            "error_rate": {"warning": 0.01, "critical": 0.05},  # percentage
            "cpu_usage": {"warning": 80, "critical": 90},  # percentage
            "memory_usage": {"warning": 80, "critical": 90},  # percentage
            "request_throughput": {"warning": 1000, "critical": 1500}  # req/s
        },
        "trend_analysis": {
            "window_size": 5,  # Number of data points to consider for trend
            "increasing_trend_threshold": 0.2,  # 20% increase over window
            "decreasing_trend_threshold": -0.2  # 20% decrease over window
        },
        "anomaly_detection": {
            "contamination": 0.1,  # Expected proportion of outliers
            "n_estimators": 100,
            "random_state": 42,
            "training_window_days": 7  # Days of historical data to use for training
        },
        "alert_cooldown_minutes": 30,
        "min_confidence_threshold": 0.7
    }
    
    @classmethod
    def get_name(cls) -> str:
        return "predictive_alerting"
    
    def __init__(self):
        self.models = {}  # One model per metric
        self.scalers = {}  # One scaler per metric
        self.last_alert_time = {}
        self.historical_data = {}
    
    async def execute(self, context: DecisionContext, 
                     config: Optional[Dict[str, Any]] = None) -> AlgorithmResult:
        """Execute the predictive alerting algorithm."""
        config = {**self.DEFAULT_CONFIG, **(config or {})}
        
        try:
            # Initialize result variables
            actions = []
            metrics = context.metrics or {}
            
            # Process each monitored metric
            for metric_name in config["metrics_to_monitor"]:
                if metric_name not in metrics:
                    continue
                
                # Get current metric value and history
                current_value = metrics[metric_name]
                self._update_historical_data(metric_name, current_value, config)
                
                # Check for threshold violations
                threshold_alert = self._check_thresholds(
                    metric_name, current_value, config
                )
                
                # Check for trend anomalies
                trend_alert = self._check_trends(
                    metric_name, current_value, config
                )
                
                # Check for statistical anomalies
                anomaly_alert = await self._check_anomalies(
                    metric_name, current_value, config
                )
                
                # Generate actions based on alerts
                if threshold_alert:
                    actions.append(threshold_alert)
                if trend_alert and self._is_above_confidence(trend_alert, config):
                    actions.append(trend_alert)
                if anomaly_alert and self._is_above_confidence(anomaly_alert, config):
                    actions.append(anomaly_alert)
            
            return AlgorithmResult(
                algorithm_name=self.get_name(),
                confidence=0.9,  # High confidence in the alerts
                recommended_actions=actions,
                metadata={
                    "metrics_checked": len(config["metrics_to_monitor"]),
                    "alerts_generated": len(actions),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error in predictive alerting: {e}", exc_info=True)
            return AlgorithmResult(
                algorithm_name=self.get_name(),
                confidence=0.0,
                recommended_actions=[],
                metadata={"error": str(e)}
            )
    
    def _update_historical_data(self, metric_name: str, current_value: float,
                              config: Dict[str, Any]) -> None:
        """Update historical data for the given metric."""
        if metric_name not in self.historical_data:
            self.historical_data[metric_name] = []
        
        # Add current value with timestamp
        self.historical_data[metric_name].append({
            "timestamp": datetime.utcnow(),
            "value": current_value
        })
        
        # Keep only data within the training window
        window_start = datetime.utcnow() - timedelta(
            days=config["anomaly_detection"]["training_window_days"]
        )
        self.historical_data[metric_name] = [
            point for point in self.historical_data[metric_name]
            if point["timestamp"] >= window_start
        ]
    
    def _check_thresholds(self, metric_name: str, current_value: float,
                         config: Dict[str, Any]) -> Optional[Action]:
        """Check if the metric has exceeded any thresholds."""
        thresholds = config["thresholds"].get(metric_name, {})
        
        # Check critical threshold
        if "critical" in thresholds and current_value >= thresholds["critical"]:
            return self._create_alert(
                metric_name=metric_name,
                current_value=current_value,
                alert_type="threshold_exceeded",
                severity="critical",
                message=f"{metric_name} exceeded critical threshold of {thresholds['critical']}",
                config=config
            )
        
        # Check warning threshold
        if "warning" in thresholds and current_value >= thresholds["warning"]:
            return self._create_alert(
                metric_name=metric_name,
                current_value=current_value,
                alert_type="threshold_warning",
                severity="warning",
                message=f"{metric_name} exceeded warning threshold of {thresholds['warning']}",
                config=config
            )
        
        return None
    
    def _check_trends(self, metric_name: str, current_value: float,
                      config: Dict[str, Any]) -> Optional[Action]:
        """Check for significant trends in the metric."""
        history = self.historical_data.get(metric_name, [])
        window_size = config["trend_analysis"]["window_size"]
        
        if len(history) < window_size + 1:
            return None
        
        # Get recent values
        recent_values = [point["value"] for point in history[-window_size:]]
        
        # Calculate trend (simple linear regression slope)
        x = np.arange(len(recent_values))
        y = np.array(recent_values)
        z = np.polyfit(x, y, 1)
        slope = z[0]
        
        # Calculate percentage change
        if len(recent_values) >= 2:
            pct_change = (recent_values[-1] - recent_values[0]) / recent_values[0]
        else:
            pct_change = 0
        
        # Check for increasing trend
        if pct_change > config["trend_analysis"]["increasing_trend_threshold"]:
            return self._create_alert(
                metric_name=metric_name,
                current_value=current_value,
                alert_type="increasing_trend",
                severity="warning",
                message=(
                    f"{metric_name} shows an increasing trend "
                    f"({pct_change:.1%} over last {window_size} points)"
                ),
                config=config,
                metadata={
                    "trend_slope": float(slope),
                    "pct_change": float(pct_change),
                    "window_size": window_size
                },
                confidence=min(0.9, 0.5 + abs(pct_change) * 2)  # Scale confidence with trend strength
            )
        
        # Check for decreasing trend
        if pct_change < config["trend_analysis"]["decreasing_trend_threshold"]:
            return self._create_alert(
                metric_name=metric_name,
                current_value=current_value,
                alert_type="decreasing_trend",
                severity="info",
                message=(
                    f"{metric_name} shows a decreasing trend "
                    f"({pct_change:.1%} over last {window_size} points)"
                ),
                config=config,
                metadata={
                    "trend_slope": float(slope),
                    "pct_change": float(pct_change),
                    "window_size": window_size
                },
                confidence=min(0.9, 0.5 + abs(pct_change) * 2)
            )
        
        return None
    
    async def _check_anomalies(self, metric_name: str, current_value: float,
                             config: Dict[str, Any]) -> Optional[Action]:
        """Check for statistical anomalies in the metric."""
        history = self.historical_data.get(metric_name, [])
        
        if len(history) < 10:  # Need sufficient data for anomaly detection
            return None
        
        # Initialize model if needed
        if metric_name not in self.models:
            self.models[metric_name] = IsolationForest(
                contamination=config["anomaly_detection"]["contamination"],
                n_estimators=config["anomaly_detection"]["n_estimators"],
                random_state=config["anomaly_detection"]["random_state"]
            )
            self.scalers[metric_name] = StandardScaler()
            
            # Train initial model
            values = np.array([point["value"] for point in history]).reshape(-1, 1)
            scaled_values = self.scalers[metric_name].fit_transform(values)
            self.models[metric_name].fit(scaled_values)
            
            return None  # Skip anomaly detection on first run
        
        # Prepare current value for prediction
        current_scaled = self.scalers[metric_name].transform(
            np.array([[current_value]])
        )
        
        # Predict anomaly (1 for inlier, -1 for outlier)
        is_anomaly = self.models[metric_name].predict(current_scaled)[0] == -1
        anomaly_score = self.models[metric_name].score_samples(current_scaled)[0]
        
        # Convert to confidence (0-1 where 1 is most anomalous)
        confidence = 1.0 - (anomaly_score / self.models[metric_name].offset_ + 1) / 2
        
        if is_anomaly and confidence > 0.7:  # Only alert on high-confidence anomalies
            return self._create_alert(
                metric_name=metric_name,
                current_value=current_value,
                alert_type="anomaly_detected",
                severity="warning",
                message=(
                    f"Anomaly detected in {metric_name}: "
                    f"value = {current_value:.2f} (anomaly score: {anomaly_score:.3f})"
                ),
                config=config,
                metadata={
                    "anomaly_score": float(anomaly_score),
                    "confidence": float(confidence),
                    "is_anomaly": bool(is_anomaly)
                },
                confidence=float(confidence)
            )
        
        # Retrain model periodically
        if len(history) % 100 == 0:  # Retrain every 100 data points
            values = np.array([point["value"] for point in history]).reshape(-1, 1)
            scaled_values = self.scalers[metric_name].fit_transform(values)
            self.models[metric_name].fit(scaled_values)
        
        return None
    
    def _create_alert(self, metric_name: str, current_value: float,
                     alert_type: str, severity: str, message: str,
                     config: Dict[str, Any],
                     metadata: Optional[Dict[str, Any]] = None,
                     confidence: float = 0.9) -> Optional[Action]:
        """Create an alert action if not in cooldown."""
        alert_key = f"{metric_name}:{alert_type}"
        
        # Check cooldown
        if alert_key in self.last_alert_time:
            last_alert = self.last_alert_time[alert_key]
            cooldown = timedelta(minutes=config["alert_cooldown_minutes"])
            
            if datetime.utcnow() - last_alert < cooldown:
                return None  # Skip alert due to cooldown
        
        # Update last alert time
        self.last_alert_time[alert_key] = datetime.utcnow()
        
        # Determine priority based on severity
        priority = {
            "critical": 100,
            "error": 90,
            "warning": 70,
            "info": 50
        }.get(severity.lower(), 50)
        
        return Action(
            action_type="create_alert",
            params={
                "metric": metric_name,
                "current_value": current_value,
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            },
            priority=priority,
            description=f"{severity.upper()}: {message}",
            source_algorithm=self.get_name(),
            metadata={
                "confidence": confidence,
                **metadata
            }
        )
    
    def _is_above_confidence(self, alert: Action, config: Dict[str, Any]) -> bool:
        """Check if the alert meets the minimum confidence threshold."""
        confidence = alert.metadata.get("confidence", 1.0)
        return confidence >= config.get("min_confidence_threshold", 0.7)
