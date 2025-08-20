# Installation et Configuration IA Supervisor

## Vue d'ensemble

L'IA Supervisor est un module intelligent pour SmartLinks DG qui fournit des capacités d'analyse, de diagnostic et de prise de décision automatisée via OpenAI GPT-4o/O3.

## Architecture

```
src/soft/dg/
├── ai/
│   ├── openai_factory.py      # Factory OpenAI avec gestion d'erreurs
│   ├── supervisor.py          # Logique métier IA Supervisor
│   └── openai_integration.py  # [Legacy] Ancienne intégration
├── api/
│   ├── endpoints/
│   │   └── ia_supervisor_v2.py # Endpoints FastAPI robustes
│   └── router.py              # Router principal
└── dependencies.py            # Injection de dépendances
```

## Installation

### 1. Dépendances Python

```bash
# Installation des dépendances
pip install -r requirements.txt

# Ou installation manuelle des packages IA
pip install openai>=1.40.0 jinja2>=3.1.6 pandas>=2.3.1
```

### 2. Configuration OpenAI

Copiez `.env.example` vers `.env` et configurez votre clé API :

```bash
cp .env.example .env
```

Éditez `.env` :
```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
OPENAI_MODEL=gpt-4o
OPENAI_API_BASE=

# Optional: O3 High Reasoning (quand disponible)
# OPENAI_MODEL=o3-high-reasoning
```

### 3. Vérification de l'installation

Lancez le selfcheck pour vérifier que tout fonctionne :

```bash
# Via l'API (serveur démarré)
curl http://localhost:8000/api/ia/selfcheck

# Ou via Python
python -c "
import asyncio
from src.soft.dg.ai.supervisor import IASupervisor
supervisor = IASupervisor()
result = asyncio.run(supervisor.selfcheck())
print(result)
"
```

## Utilisation

### Démarrage du serveur

```bash
# Démarrage standard
python main.py

# Ou avec uvicorn directement
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Endpoints disponibles

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/ia/ask` | POST | Poser une question à l'IA |
| `/api/ia/analyze` | GET | Analyser l'état du système |
| `/api/ia/fix` | POST | Corriger les issues détectées |
| `/api/ia/status` | GET | Statut actuel du supervisor |
| `/api/ia/switch-mode` | POST | Changer le mode d'opération |
| `/api/ia/selfcheck` | GET | Diagnostic complet |
| `/api/ia/health` | GET | Vérification de santé simple |
| `/api/ia/algorithms` | GET | Liste des algorithmes |
| `/api/ia/logs` | GET | Logs d'interaction |

### Exemples d'utilisation

#### Poser une question
```bash
curl -X POST "http://localhost:8000/api/ia/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Quel est l'état actuel du système?"}'
```

#### Analyser le système
```bash
curl "http://localhost:8000/api/ia/analyze"
```

#### Changer le mode d'opération
```bash
curl -X POST "http://localhost:8000/api/ia/switch-mode" \
  -H "Content-Type: application/json" \
  -d '{"mode": "sandbox"}'
```

## Modes d'opération

- **AUTO** : Mode autonome, exécute les actions automatiquement
- **MANUAL** : Mode manuel, requiert approbation humaine
- **SANDBOX** : Mode simulation, simule sans exécuter

## Mode dégradé

Si OpenAI est indisponible, l'IA Supervisor fonctionne en mode dégradé :
- Les questions retournent "Fonctionnalité IA indisponible"
- Les analyses utilisent des réponses par défaut
- Le système continue de fonctionner sans IA

## Troubleshooting

### Erreur "OpenAI API key not found"
- Vérifiez que `OPENAI_API_KEY` est défini dans `.env`
- Vérifiez que la clé API est valide

### Erreur "Rate limit exceeded"
- L'IA Supervisor gère automatiquement les retry
- En cas de limite persistante, attendez ou upgradez votre plan OpenAI

### Mode dégradé persistant
- Vérifiez votre connexion internet
- Testez votre clé API avec `curl` directement
- Consultez les logs pour plus de détails

### Logs et debugging

```bash
# Voir les logs en temps réel
tail -f autopilot.log

# Logs spécifiques IA
grep "IASupervisor\|OpenAI" autopilot.log
```

## Développement

### Ajouter de nouveaux algorithmes

1. Créez un fichier dans `src/soft/dg/algorithms/`
2. Implémentez la classe avec `get_name()` et `execute()` async
3. L'algorithme sera automatiquement découvert au démarrage

### Personnaliser les prompts

Modifiez les prompts dans `supervisor.py` méthode `_get_ai_analysis()`.

### Tests

```bash
# Tests unitaires
python -m pytest tests/test_ia_supervisor.py

# Test d'intégration
python tests/test_app_integration.py
```

## Sécurité

- ⚠️ **Jamais** de clé API hardcodée dans le code
- Utilisez toujours `.env` pour les secrets
- Limitez les permissions de votre clé OpenAI
- Surveillez l'usage via le dashboard OpenAI

## Performance

- Timeout par défaut : 30 secondes
- Retry automatique : 3 tentatives
- Cache des réponses : Non implémenté (à ajouter si besoin)
- Rate limiting : Géré par OpenAI

## Support O3 High Reasoning

Quand O3 sera disponible, changez simplement :
```env
OPENAI_MODEL=o3-high-reasoning
```

Le système basculera automatiquement vers O3 avec fallback sur GPT-4o.
