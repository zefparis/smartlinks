# IA Supervisor API Reference

## Endpoints de base

### POST /api/ia/ask
Pose une question à l'IA Supervisor.

**Request Body:**
```json
{
  "question": "string (required)",
  "context": {
    "key": "value"
  }
}
```

**Response:**
```json
{
  "question": "string",
  "response": "string", 
  "timestamp": "2024-01-01T12:00:00Z",
  "degraded_mode": false
}
```

### GET /api/ia/analyze
Analyse complète du système.

**Response:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "algorithms_executed": ["algo1", "algo2"],
  "results": {
    "algo1": {"status": "success"},
    "algo2": {"status": "error", "message": "..."}
  },
  "ai_analysis": {
    "summary": "Résumé de l'analyse",
    "key_findings": ["finding1", "finding2"],
    "recommendations": ["rec1", "rec2"],
    "confidence_score": 0.85
  },
  "recommended_actions": [
    {
      "action_type": "restart_service",
      "priority": "high",
      "source_algorithm": "algo1"
    }
  ],
  "degraded_mode": false
}
```

### POST /api/ia/fix
Corrige automatiquement les issues détectées.

**Response:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "actions_executed": 3,
  "results": [
    {
      "status": "success",
      "action": {"action_type": "restart_service"},
      "result": "Service redémarré avec succès"
    }
  ],
  "mode": "auto"
}
```

### GET /api/ia/status
Statut actuel du supervisor.

**Response:**
```json
{
  "mode": "auto",
  "degraded_mode": false,
  "last_analysis_time": "2024-01-01T12:00:00Z",
  "last_action_time": "2024-01-01T12:00:00Z", 
  "active_actions": 0,
  "available_algorithms": ["security_scan", "performance_check"],
  "openai_status": "ready",
  "is_ready": true,
  "metrics": {
    "interaction_log": []
  }
}
```

### POST /api/ia/switch-mode
Change le mode d'opération.

**Request Body:**
```json
{
  "mode": "auto|manual|sandbox"
}
```

**Response:** Même format que `/api/ia/status`

### GET /api/ia/selfcheck
Diagnostic complet du système.

**Response:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "global_status": "ready|degraded|unavailable",
  "supervisor_status": {
    "mode": "auto",
    "degraded_mode": false,
    "algorithms_count": 5,
    "last_analysis": "2024-01-01T12:00:00Z"
  },
  "openai_status": {
    "status": "ready",
    "model": "gpt-4o",
    "api_key_configured": true,
    "last_check": "2024-01-01T12:00:00Z",
    "tests": {
      "config": {"passed": true, "message": "Clé API configurée"},
      "connectivity": {"passed": true, "message": "Connexion OK"},
      "simple_request": {"passed": true, "message": "Réponse: OK"}
    }
  },
  "tests": {
    "algorithms": {
      "count": 5,
      "list": ["algo1", "algo2"],
      "passed": true,
      "message": "5 algorithmes chargés"
    },
    "analysis": {
      "passed": true,
      "message": "Analyse IA fonctionnelle"
    },
    "question": {
      "passed": true,
      "message": "Réponse: OK..."
    }
  }
}
```

## Endpoints utilitaires

### GET /api/ia/health
Vérification de santé simple.

**Response:**
```json
{
  "status": "healthy|degraded",
  "timestamp": "2024-01-01T12:00:00Z",
  "openai_available": true,
  "algorithms_count": 5
}
```

### GET /api/ia/algorithms
Liste des algorithmes disponibles.

**Response:**
```json
["security_scan", "performance_check", "maintenance_check"]
```

### GET /api/ia/logs?limit=100
Logs d'interaction récents.

**Query Parameters:**
- `limit`: Nombre max de logs (1-1000, défaut: 100)

**Response:**
```json
[
  {
    "timestamp": "2024-01-01T12:00:00Z",
    "type": "question",
    "content": "Quel est l'état du système?",
    "response": "Le système fonctionne normalement",
    "context": {}
  }
]
```

## Codes d'erreur

### 400 Bad Request
- Mode invalide lors du switch-mode
- Paramètres de requête invalides

### 500 Internal Server Error  
- Erreur interne du supervisor
- Problème avec les algorithmes
- Erreur de parsing des réponses IA

### 503 Service Unavailable
- Service temporairement indisponible
- Problème de connectivité majeur

## Modèles de données

### ErrorResponse
```json
{
  "error": "string",
  "detail": "string", 
  "timestamp": "2024-01-01T12:00:00Z",
  "status_code": 500
}
```

### Modes d'opération
- `auto`: Exécution automatique des actions
- `manual`: Approbation humaine requise  
- `sandbox`: Simulation sans exécution

### Statuts OpenAI
- `ready`: Fonctionnel
- `degraded`: Partiellement fonctionnel
- `unavailable`: Indisponible
- `error`: Erreur de configuration

## Exemples d'intégration

### Python
```python
import httpx

async def ask_ia(question: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/ia/ask",
            json={"question": question}
        )
        return response.json()

# Usage
result = await ask_ia("Analyse l'état du système")
print(result["response"])
```

### JavaScript
```javascript
async function analyzeSystem() {
    const response = await fetch('http://localhost:8000/api/ia/analyze');
    const data = await response.json();
    
    if (data.degraded_mode) {
        console.warn('IA en mode dégradé');
    }
    
    return data.ai_analysis;
}
```

### cURL
```bash
# Question simple
curl -X POST "http://localhost:8000/api/ia/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Status du système?"}'

# Selfcheck complet
curl "http://localhost:8000/api/ia/selfcheck" | jq .

# Changer en mode sandbox
curl -X POST "http://localhost:8000/api/ia/switch-mode" \
  -H "Content-Type: application/json" \
  -d '{"mode": "sandbox"}'
```
