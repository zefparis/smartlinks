# SmartLinks Frontend - API Schemas Documentation

## 📋 Overview

Ce document décrit les formats de données attendus par le frontend React et les réponses réelles des endpoints backend FastAPI.

## 🔧 Corrections Apportées

### 1. **Schema Alignment Issues Fixed**

- ✅ **DeviceStats.count vs backend.clicks** - API client mappe automatiquement `clicks` → `count`
- ✅ **Wrapped responses** - Backend retourne `{devices: [...]}` mais frontend attend `DeviceStats[]`
- ✅ **Missing endpoints** - Ajout de `/api/settings` et `/api/analytics/schema`
- ✅ **Debug logging** - Logs côté frontend et backend pour troubleshooting

### 2. **API Client Fixes (api.ts)**

```typescript
// AVANT (problématique)
getDeviceStats: () => unwrapResponse(api.get<DeviceStats[]>('/api/analytics/devices'))

// APRÈS (corrigé)
getDeviceStats: async () => {
  const response = await unwrapResponse(api.get('/api/analytics/devices'));
  console.log('DEBUG getDeviceStats response:', response);
  
  if (response && response.devices) {
    return response.devices.map((device: any) => ({
      device: device.device,
      count: device.clicks, // Map clicks to count for frontend compatibility
      conversion_rate: device.conversion_rate || 0,
      clicks: device.clicks,
      conversions: device.conversions || 0,
      revenue: device.revenue || 0
    }));
  }
  return [];
}
```

## 📊 Endpoints Analytics

### GET `/api/analytics/devices`

**Backend Response:**
```json
{
  "devices": [
    {
      "device": "mobile",
      "clicks": 15420,
      "conversions": 2313,
      "conversion_rate": 0.15,
      "revenue": 34567.89,
      "revenue_per_click": 2.24
    }
  ],
  "total_clicks": 45000,
  "total_conversions": 6750,
  "overall_conversion_rate": 0.15
}
```

**Frontend Expected (DeviceStats[]):**
```typescript
interface DeviceStats {
  device: string;
  count: number;        // Mapped from backend 'clicks'
  conversion_rate: number;
  clicks?: number;      // Backend field
  conversions?: number; // Backend field  
  revenue?: number;     // Backend field
}
```

### GET `/api/analytics/countries?days=30`

**Backend Response:**
```json
{
  "countries": [
    {
      "country": "US",
      "clicks": 12000,
      "conversions": 1800,
      "revenue": 25000.0,
      "conversion_rate": 0.15
    }
  ]
}
```

**Frontend Expected (CountryStats[]):**
```typescript
interface CountryStats {
  country: string;
  clicks: number;
  conversions: number;
  revenue: number;
}
```

### GET `/api/analytics/clicks/history?days=7`

**Backend Response:**
```json
{
  "history": [
    {
      "date": "2025-01-19",
      "clicks": 1500,
      "conversions": 225,
      "revenue": 3750.0
    }
  ],
  "total_clicks": 10500,
  "total_conversions": 1575,
  "date_range": {
    "start": "2025-01-12",
    "end": "2025-01-19"
  }
}
```

**Frontend Expected (ClickHistory[]):**
```typescript
interface ClickHistory {
  date: string;
  clicks: number;
  conversions: number;
  revenue: number;
}
```

### GET `/api/analytics/traffic-by-segment?days=30`

**Backend Response:**
```json
{
  "segments": [
    {
      "segment_id": "seg_us_mobile",
      "geo": "US",
      "device": "mobile",
      "clicks": 8500,
      "conversions": 1275,
      "revenue": 18750.0,
      "conversion_rate": 0.15,
      "revenue_per_click": 2.21
    }
  ],
  "totals": {
    "clicks": 45000,
    "conversions": 6750,
    "revenue": 125000.0,
    "conversion_rate": 0.15
  }
}
```

## ⚙️ Settings Endpoints

### GET `/api/settings`

**Backend Response:**
```json
{
  "general": {
    "app_name": "SmartLinks Autopilot",
    "version": "1.0.0",
    "timezone": "UTC",
    "currency": "EUR",
    "default_cap_day": 1000,
    "fraud_threshold": 0.8,
    "auto_approval": true,
    "email_notifications": true,
    "max_daily_budget": 5000.0
  },
  "offers": [...],
  "creators": [...],
  "segments": [...]
}
```

### PUT `/api/settings/general`

**Request:**
```json
{
  "key": "fraud_threshold",
  "value": 0.9
}
```

**Response:**
```json
{
  "success": true,
  "message": "Paramètre 'fraud_threshold' mis à jour avec succès",
  "key": "fraud_threshold",
  "value": 0.9
}
```

## 🐛 Debug Endpoints

### GET `/api/analytics/health`

Endpoint de debug pour vérifier la santé du système analytics.

### GET `/api/analytics/schema`

Endpoint spécial qui expose tous les schémas JSON attendus par le frontend. Utile pour debug et validation.

## 🔍 Debugging Tips

### Frontend Console Logs

Le client API ajoute maintenant des logs debug:
```javascript
console.log('DEBUG getDeviceStats response:', response);
console.log('DEBUG getCountryStats response:', response);
console.log('DEBUG getClickHistory response:', response);
```

### Backend Logs

Le backend log toutes les requêtes analytics:
```
Analytics request: GET /api/analytics/devices
Analytics response: 200
```

### Common Issues

1. **Empty Data Arrays** - Vérifier que la base contient des données via `/api/analytics/health`
2. **404 Errors** - Vérifier que tous les routers sont inclus dans `router.py`
3. **Type Mismatches** - Utiliser `/api/analytics/schema` pour voir les formats attendus
4. **CORS Issues** - Backend configuré pour `localhost:3000`

## 🚀 Testing

```bash
# Test all analytics endpoints
python scripts\check_analytics.py

# Test schema endpoint
curl http://localhost:8000/api/analytics/schema

# Test settings endpoint  
curl http://localhost:8000/api/settings

# Check health
curl http://localhost:8000/api/analytics/health
```

## ✅ Status

- ✅ Analytics endpoints schema alignment
- ✅ Settings endpoints added
- ✅ Debug logging implemented
- ✅ Schema documentation endpoint
- ✅ Frontend error handling improved
- ✅ API client wrapper fixes

Le dashboard analytics devrait maintenant afficher toutes les données sans erreurs 404 ou données undefined.
