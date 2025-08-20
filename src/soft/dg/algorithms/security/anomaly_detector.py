"""
Détecteur d'anomalies pour le DG autonome.

Ce module implémente un algorithme de détection d'anomalies basé sur des règles
et des seuils configurables pour identifier des comportements suspects dans le trafic.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from ...models.decision import Action, DecisionContext
from ..base import Algorithm, AlgorithmResult

logger = logging.getLogger(__name__)

class AnomalyDetector(Algorithm):
    """Détecte les anomalies dans le trafic et le comportement du système."""
    
    # Seuils par défaut (peuvent être surchargés via la config)
    DEFAULT_CONFIG = {
        "click_rate_threshold": 100,  # Nombre max de clics par minute par IP
        "conversion_rate_threshold": 0.3,  # Taux de conversion minimum suspect
        "use_ml_detection": True,  # Activer la détection par apprentissage automatique
        "ml_contamination": 0.01,  # Pourcentage attendu d'anomalies
        "min_confidence": 0.7,  # Confiance minimale pour signaler une anomalie
    }
    
    @classmethod
    def get_name(cls) -> str:
        return "anomaly_detector"
    
    def __init__(self):
        self._model = None
        self._scaler = StandardScaler()
        self._last_training = None
    
    async def execute(self, context: DecisionContext, 
                     config: Optional[Dict[str, Any]] = None) -> AlgorithmResult:
        """Exécute la détection d'anomalies sur le contexte actuel."""
        # Fusion de la configuration par défaut avec celle fournie
        config = {**self.DEFAULT_CONFIG, **(config or {})}
        
        # Extraction des métriques du contexte
        metrics = context.metrics or {}
        
        # Vérification des seuils simples
        simple_anomalies = self._check_simple_thresholds(metrics, config)
        
        # Détection avancée par ML si activée
        ml_anomalies = []
        if config["use_ml_detection"]:
            ml_anomalies = await self._check_ml_anomalies(metrics, config)
        
        # Agrégation des anomalies détectées
        all_anomalies = simple_anomalies + ml_anomalies
        
        # Création des actions recommandées
        actions = []
        confidence = 0.0
        
        if all_anomalies:
            # Calcul de la confiance globale (moyenne des confiances des anomalies)
            confidence = sum(a.get('confidence', 0) for a in all_anomalies) / len(all_anomalies)
            
            # Création d'actions en fonction du type d'anomalie
            for anomaly in all_anomalies:
                action = self._create_mitigation_action(anomaly, config)
                if action:
                    actions.append(action)
        
        # Mise à jour du modèle si nécessaire
        await self._update_model(metrics, config)
        
        return AlgorithmResult(
            algorithm_name=self.get_name(),
            confidence=confidence,
            recommended_actions=actions,
            metadata={
                "anomalies_detected": len(all_anomalies),
                "anomaly_details": all_anomalies,
                "config_used": config
            }
        )
    
    def _check_simple_thresholds(self, metrics: Dict[str, Any], 
                               config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Vérifie les seuils simples pour détecter des anomalies évidentes."""
        anomalies = []
        
        # Vérification du taux de clics par IP
        if "clicks_per_ip" in metrics:
            for ip, count in metrics["clicks_per_ip"].items():
                if count > config["click_rate_threshold"]:
                    anomalies.append({
                        "type": "high_click_rate",
                        "ip": ip,
                        "count": count,
                        "threshold": config["click_rate_threshold"],
                        "confidence": 0.9,  # Haute confiance pour ce type d'anomalie
                        "severity": "high"
                    })
        
        # Vérification du taux de conversion anormalement bas
        if "conversion_rate" in metrics:
            conv_rate = metrics["conversion_rate"]
            if conv_rate < config["conversion_rate_threshold"]:
                anomalies.append({
                    "type": "low_conversion_rate",
                    "rate": conv_rate,
                    "threshold": config["conversion_rate_threshold"],
                    "confidence": 0.7,
                    "severity": "medium"
                })
        
        return anomalies
    
    async def _check_ml_anomalies(self, metrics: Dict[str, Any], 
                               config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Utilise un modèle ML pour détecter des anomalies plus subtiles."""
        # Extraction des caractéristiques pertinentes pour le modèle
        features = self._extract_features(metrics)
        
        if not features:
            return []
        
        # Vérification si le modèle est entraîné
        if self._model is None:
            self._train_model(features, config)
            return []  # Pas de détection lors du premier entraînement
        
        # Normalisation des caractéristiques
        features_scaled = self._scaler.transform([features])
        
        # Détection d'anomalie
        is_anomaly = self._model.predict(features_scaled)[0] == -1
        anomaly_score = self._model.score_samples(features_scaled)[0]
        
        if is_anomaly and -anomaly_score > config["min_confidence"]:
            return [{
                "type": "ml_anomaly",
                "score": float(anomaly_score),
                "confidence": min(0.9, -anomaly_score),  # Convertir en positif et limiter à 0.9
                "severity": "high" if -anomaly_score > 0.8 else "medium",
                "features": features
            }]
        
        return []
    
    def _extract_features(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Extrait les caractéristiques pertinentes des métriques pour le modèle ML."""
        features = {}
        
        # Exemple de caractéristiques (à adapter selon les besoins)
        if "clicks_per_minute" in metrics:
            features["clicks_per_minute"] = float(metrics["clicks_per_minute"])
        
        if "conversion_rate" in metrics:
            features["conversion_rate"] = float(metrics["conversion_rate"])
        
        if "avg_session_duration" in metrics:
            features["avg_session_duration"] = float(metrics["avg_session_duration"])
        
        if "bounce_rate" in metrics:
            features["bounce_rate"] = float(metrics["bounce_rate"])
        
        return features
    
    def _train_model(self, features: Dict[str, float], config: Dict[str, Any]):
        """Entraîne le modèle de détection d'anomalies."""
        # Pour l'instant, on initialise simplement un modèle vide
        # Dans une implémentation réelle, on utiliserait des données historiques
        self._model = IsolationForest(
            contamination=config["ml_contamination"],
            random_state=42
        )
        
        # Initialisation du scaler avec des valeurs par défaut
        # (dans un cas réel, on utiliserait des données d'entraînement)
        default_values = [
            [0.0],  # clicks_per_minute
            [0.1],  # conversion_rate
            [60.0],  # avg_session_duration
            [0.5]    # bounce_rate
        ]
        self._scaler.fit(default_values)
        
        self._last_training = datetime.utcnow()
        logger.info("Modèle de détection d'anomalies initialisé")
    
    async def _update_model(self, metrics: Dict[str, Any], config: Dict[str, Any]):
        """Met à jour le modèle avec les nouvelles données."""
        # Dans une implémentation réelle, on mettrait à jour le modèle périodiquement
        # avec les nouvelles données pour s'adapter aux changements de comportement
        
        # Pour l'instant, on se contente de réentraîner périodiquement
        if (self._last_training is None or 
            datetime.utcnow() - self._last_training > timedelta(hours=24)):
            logger.info("Mise à jour périodique du modèle de détection d'anomalies")
            features = self._extract_features(metrics)
            if features:
                self._train_model(features, config)
    
    def _create_mitigation_action(self, anomaly: Dict[str, Any], 
                                config: Dict[str, Any]) -> Optional[Action]:
        """Crée une action de mitigation pour une anomalie détectée."""
        anomaly_type = anomaly.get("type")
        
        if anomaly_type == "high_click_rate":
            return Action(
                action_type="throttle_ip",
                params={
                    "ip": anomaly["ip"],
                    "duration_minutes": 60,
                    "reason": f"Taux de clics anormalement élevé: {anomaly['count']}/min"
                },
                priority=80 if anomaly.get("severity") == "high" else 60,
                description=f"Limiter le trafic de l'IP {anomaly['ip']} (taux de clics anormal)"
            )
        
        elif anomaly_type == "low_conversion_rate":
            return Action(
                action_type="investigate_traffic_quality",
                params={
                    "metric": "conversion_rate",
                    "value": anomaly["rate"],
                    "threshold": anomaly["threshold"]
                },
                priority=70,
                description="Enquêter sur la qualité du trafic (taux de conversion bas)"
            )
        
        elif anomaly_type == "ml_anomaly":
            return Action(
                action_type="investigate_anomaly",
                params={
                    "anomaly_type": "machine_learning",
                    "score": anomaly["score"],
                    "features": anomaly.get("features", {})
                },
                priority=90 if anomaly.get("severity") == "high" else 70,
                description=f"Anomalie détectée par ML (score: {anomaly['score']:.2f})"
            )
        
        return None
