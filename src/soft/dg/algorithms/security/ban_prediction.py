"""
Ban Prediction Algorithm for SmartLinks Autonomous DG.

This algorithm predicts the risk of account bans based on various signals
and patterns in the traffic and user behavior.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from ...models.decision import Action, DecisionContext
from ..base import Algorithm, AlgorithmResult

logger = logging.getLogger(__name__)

class BanPredictionAlgorithm(Algorithm):
    """Algorithm for predicting account ban risks."""
    
    # Default configuration
    DEFAULT_CONFIG = {
        "risk_threshold": 0.7,  # Threshold for high risk
        "warning_threshold": 0.4,  # Threshold for medium risk
        "features": [
            "click_through_rate",
            "conversion_rate",
            "bounce_rate",
            "session_duration_avg",
            "requests_per_second",
            "error_rate",
            "new_user_ratio"
        ],
        "weights": {
            "click_through_rate": 0.2,
            "conversion_rate": 0.25,
            "bounce_rate": 0.15,
            "session_duration_avg": 0.1,
            "requests_per_second": 0.2,
            "error_rate": 0.05,
            "new_user_ratio": 0.05
        },
        "time_windows": ["1h", "6h", "24h"],
        "model_params": {
            "contamination": 0.1,
            "random_state": 42,
            "n_estimators": 100
        }
    }
    
    @classmethod
    def get_name(cls) -> str:
        return "ban_prediction"
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.last_trained = None
    
    async def execute(self, context: DecisionContext, 
                     config: Optional[Dict[str, Any]] = None) -> AlgorithmResult:
        """Execute the ban prediction algorithm.
        
        Args:
            context: Current decision context
            config: Algorithm configuration (overrides defaults)
            
        Returns:
            AlgorithmResult containing risk assessment and recommended actions
        """
        # Merge default config with provided config
        config = {**self.DEFAULT_CONFIG, **(config or {})}
        
        try:
            # Extract and prepare features
            features = self._extract_features(context, config)
            
            # Train or update model if needed
            if self._needs_retraining():
                await self._train_model(features, config)
            
            # Predict risk
            risk_score = self._predict_risk(features, config)
            
            # Generate actions based on risk level
            actions = self._generate_actions(risk_score, context, config)
            
            # Prepare metadata for the result
            metadata = {
                "risk_score": risk_score,
                "features": features,
                "risk_level": self._get_risk_level(risk_score, config),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return AlgorithmResult(
                algorithm_name=self.get_name(),
                confidence=abs(risk_score - 0.5) * 2,  # Confidence is highest at extremes
                recommended_actions=actions,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error in ban prediction: {e}", exc_info=True)
            return AlgorithmResult(
                algorithm_name=self.get_name(),
                confidence=0.0,
                recommended_actions=[],
                metadata={"error": str(e), "timestamp": datetime.utcnow().isoformat()}
            )
    
    def _extract_features(self, context: DecisionContext, config: Dict[str, Any]) -> Dict[str, float]:
        """Extract and normalize features from the decision context."""
        features = {}
        
        # Extract basic metrics
        metrics = context.metrics or {}
        for feature in config["features"]:
            features[feature] = float(metrics.get(feature, 0.0))
        
        # Calculate additional derived features
        if "click_through_rate" not in features and all(k in metrics for k in ["clicks", "impressions"]):
            features["click_through_rate"] = metrics["clicks"] / max(1, metrics["impressions"])
        
        if "conversion_rate" not in features and all(k in metrics for k in ["conversions", "clicks"]):
            features["conversion_rate"] = metrics["conversions"] / max(1, metrics["clicks"])
        
        if "bounce_rate" not in features and "bounces" in metrics and "sessions" in metrics:
            features["bounce_rate"] = metrics["bounces"] / max(1, metrics["sessions"])
        
        # Apply weights to features
        for feature, weight in config.get("weights", {}).items():
            if feature in features:
                features[feature] *= weight
        
        return features
    
    def _needs_retraining(self) -> bool:
        """Determine if the model needs to be retrained."""
        if self.model is None or self.last_trained is None:
            return True
        
        # Retrain every 24 hours
        return (datetime.utcnow() - self.last_trained) > timedelta(hours=24)
    
    async def _train_model(self, features: Dict[str, float], config: Dict[str, Any]) -> None:
        """Train or update the risk prediction model."""
        # In a real implementation, this would use historical data
        # For now, we'll use a simple Isolation Forest
        
        # Convert features to array format expected by scikit-learn
        feature_array = np.array([[features.get(f, 0) for f in config["features"]]])
        
        # Scale features
        self.scaler.fit(feature_array)
        scaled_features = self.scaler.transform(feature_array)
        
        # Train model
        self.model = IsolationForest(**config["model_params"])
        self.model.fit(scaled_features)
        
        self.last_trained = datetime.utcnow()
        logger.info("Ban prediction model trained successfully")
    
    def _predict_risk(self, features: Dict[str, float], config: Dict[str, Any]) -> float:
        """Predict the risk of ban based on current features."""
        if self.model is None:
            # If model isn't trained yet, return a default risk
            return 0.5
        
        # Prepare features for prediction
        feature_array = np.array([[features.get(f, 0) for f in config["features"]]])
        scaled_features = self.scaler.transform(feature_array)
        
        # Get anomaly score (lower means more anomalous)
        anomaly_score = self.model.score_samples(scaled_features)[0]
        
        # Convert to risk score (0-1 where 1 is highest risk)
        risk_score = 1.0 - ((anomaly_score + 0.5) / 1.0)  # Convert from [-0.5, 0.5] to [0, 1]
        
        return max(0.0, min(1.0, risk_score))  # Clamp to [0, 1]
    
    def _get_risk_level(self, risk_score: float, config: Dict[str, Any]) -> str:
        """Convert risk score to a human-readable level."""
        if risk_score >= config["risk_threshold"]:
            return "high"
        elif risk_score >= config["warning_threshold"]:
            return "medium"
        return "low"
    
    def _generate_actions(self, risk_score: float, 
                         context: DecisionContext,
                         config: Dict[str, Any]) -> List[Action]:
        """Generate recommended actions based on risk level."""
        risk_level = self._get_risk_level(risk_score, config)
        actions = []
        
        if risk_level == "high":
            actions.append(Action(
                action_type="throttle_traffic",
                params={"percentage": 70, "duration_minutes": 60},
                priority=90,
                description="Throttle traffic by 70% due to high ban risk",
                source_algorithm=self.get_name()
            ))
            actions.append(Action(
                action_type="alert_team",
                params={
                    "level": "critical",
                    "message": f"High ban risk detected: {risk_score:.2f}",
                    "metrics": {k: v for k, v in context.metrics.items() if k in config["features"]}
                },
                priority=100,
                description="Alert team about high ban risk",
                source_algorithm=self.get_name()
            ))
        elif risk_level == "medium":
            actions.append(Action(
                action_type="throttle_traffic",
                params={"percentage": 30, "duration_minutes": 30},
                priority=70,
                description="Throttle traffic by 30% due to medium ban risk",
                source_algorithm=self.get_name()
            ))
            actions.append(Action(
                action_type="monitor_metrics",
                params={
                    "metrics": config["features"],
                    "interval_seconds": 300,
                    "duration_minutes": 60
                },
                priority=50,
                description="Monitor key metrics closely",
                source_algorithm=self.get_name()
            ))
        
        # Always add a monitoring action for low risk
        actions.append(Action(
            action_type="monitor_metrics",
            params={
                "metrics": config["features"],
                "interval_seconds": 900,
                "duration_minutes": 240
            },
            priority=30,
            description="Routine monitoring of ban risk factors",
            source_algorithm=self.get_name()
        ))
        
        return actions
