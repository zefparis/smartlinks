"""Feature Store service for online and offline features."""

import json
import redis
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..pac.models import FeatureSnapshot
from ..pac.schemas import FeatureSnapshot as FeatureSnapshotSchema

class FeatureService:
    """Feature store service."""
    
    def __init__(self, db: Session, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.redis = redis_client or redis.Redis(host='localhost', port=6379, db=0)
        self.online_ttl = 3600  # 1 hour TTL for online features
    
    async def set_online_feature(self, key: str, value: Dict[str, Any], 
                                tenant_id: Optional[str] = None):
        """Set online feature in Redis."""
        feature_key = self._build_feature_key(key, tenant_id)
        
        feature_data = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": tenant_id
        }
        
        self.redis.setex(
            feature_key,
            self.online_ttl,
            json.dumps(feature_data)
        )
    
    async def get_online_feature(self, key: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get online feature from Redis."""
        feature_key = self._build_feature_key(key, tenant_id)
        
        data = self.redis.get(feature_key)
        if not data:
            return None
        
        feature_data = json.loads(data)
        return feature_data["value"]
    
    async def get_online_features(self, keys: List[str], tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get multiple online features."""
        features = {}
        
        for key in keys:
            value = await self.get_online_feature(key, tenant_id)
            if value is not None:
                features[key] = value
        
        return features
    
    async def snapshot_feature(self, key: str, value: Dict[str, Any], source: str,
                              tenant_id: Optional[str] = None) -> str:
        """Create offline feature snapshot."""
        snapshot_id = f"snap_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{key}"
        
        snapshot = FeatureSnapshot(
            id=snapshot_id,
            ts=datetime.utcnow(),
            key=key,
            value_json=value,
            source=source,
            tenant_id=tenant_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(snapshot)
        self.db.commit()
        
        return snapshot_id
    
    async def get_features_at_time(self, timestamp: datetime, 
                                  horizon_minutes: int = 60,
                                  tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get features at a specific timestamp for replay."""
        start_time = timestamp - timedelta(minutes=horizon_minutes)
        end_time = timestamp + timedelta(minutes=horizon_minutes)
        
        # Query snapshots within time window
        query = self.db.query(FeatureSnapshot).filter(
            and_(
                FeatureSnapshot.ts >= start_time,
                FeatureSnapshot.ts <= end_time
            )
        )
        
        if tenant_id:
            query = query.filter(FeatureSnapshot.tenant_id == tenant_id)
        
        snapshots = query.order_by(desc(FeatureSnapshot.ts)).all()
        
        # Get latest value for each key
        features = {}
        seen_keys = set()
        
        for snapshot in snapshots:
            if snapshot.key not in seen_keys:
                features[snapshot.key] = snapshot.value_json
                seen_keys.add(snapshot.key)
        
        return features
    
    async def get_feature_history(self, key: str, start_time: datetime, end_time: datetime,
                                 tenant_id: Optional[str] = None) -> List[FeatureSnapshotSchema]:
        """Get feature history for backtesting."""
        query = self.db.query(FeatureSnapshot).filter(
            and_(
                FeatureSnapshot.key == key,
                FeatureSnapshot.ts >= start_time,
                FeatureSnapshot.ts <= end_time
            )
        )
        
        if tenant_id:
            query = query.filter(FeatureSnapshot.tenant_id == tenant_id)
        
        snapshots = query.order_by(FeatureSnapshot.ts).all()
        
        return [
            FeatureSnapshotSchema(
                id=snap.id,
                ts=snap.ts,
                key=snap.key,
                value=snap.value_json,
                source=snap.source,
                tenant_id=snap.tenant_id,
                created_at=snap.created_at
            )
            for snap in snapshots
        ]
    
    async def check_feature_freshness(self, key: str, max_age_minutes: int = 60,
                                     tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Check feature freshness and detect drift."""
        # Check online feature
        online_feature = await self.get_online_feature(key, tenant_id)
        
        # Get latest offline snapshot
        query = self.db.query(FeatureSnapshot).filter(FeatureSnapshot.key == key)
        if tenant_id:
            query = query.filter(FeatureSnapshot.tenant_id == tenant_id)
        
        latest_snapshot = query.order_by(desc(FeatureSnapshot.ts)).first()
        
        result = {
            "key": key,
            "online_available": online_feature is not None,
            "offline_available": latest_snapshot is not None,
            "fresh": False,
            "age_minutes": None,
            "drift_detected": False
        }
        
        if latest_snapshot:
            age = datetime.utcnow() - latest_snapshot.ts
            result["age_minutes"] = age.total_seconds() / 60
            result["fresh"] = result["age_minutes"] <= max_age_minutes
            
            # Simple drift detection: compare online vs offline
            if online_feature and latest_snapshot.value_json:
                result["drift_detected"] = self._detect_drift(
                    online_feature, latest_snapshot.value_json
                )
        
        return result
    
    def _build_feature_key(self, key: str, tenant_id: Optional[str] = None) -> str:
        """Build Redis key for feature."""
        if tenant_id:
            return f"features:{tenant_id}:{key}"
        return f"features:global:{key}"
    
    def _detect_drift(self, online_value: Dict[str, Any], offline_value: Dict[str, Any]) -> bool:
        """Simple drift detection between online and offline features."""
        # Compare numeric values with 10% threshold
        for key in set(online_value.keys()) & set(offline_value.keys()):
            online_val = online_value.get(key)
            offline_val = offline_value.get(key)
            
            if isinstance(online_val, (int, float)) and isinstance(offline_val, (int, float)):
                if offline_val != 0:
                    drift_pct = abs(online_val - offline_val) / abs(offline_val)
                    if drift_pct > 0.1:  # 10% threshold
                        return True
        
        return False

class FeatureUpdater:
    """Background service to update features."""
    
    def __init__(self, feature_service: FeatureService):
        self.feature_service = feature_service
    
    async def update_traffic_features(self, algo_key: str, metrics: Dict[str, Any]):
        """Update traffic-related features."""
        features = {
            "cvr_1h": metrics.get("cvr_1h", 0.025),
            "cvr_24h_mean": metrics.get("cvr_24h_mean", 0.028),
            "volume_1h": metrics.get("volume_1h", 1000),
            "revenue_1h": metrics.get("revenue_1h", 2500.0),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Update online features
        await self.feature_service.set_online_feature(f"traffic:{algo_key}", features)
        
        # Create offline snapshot
        await self.feature_service.snapshot_feature(
            f"traffic:{algo_key}", features, "traffic_updater"
        )
    
    async def update_segment_features(self, segment_id: str, metrics: Dict[str, Any]):
        """Update segment-specific features."""
        features = {
            "segment_cvr": metrics.get("cvr", 0.025),
            "segment_volume": metrics.get("volume", 500),
            "segment_roi": metrics.get("roi", 2.5),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await self.feature_service.set_online_feature(f"segment:{segment_id}", features)
        await self.feature_service.snapshot_feature(
            f"segment:{segment_id}", features, "segment_updater"
        )
