# SmartLinks Autopilot RCP - Guide de Déploiement

## 🎯 Fonctionnalités Implémentées

### ✅ Système RCP Core Avancé
- **Policy-as-Code (PaC)** : Gestion YAML avec validation, diff, plan/apply
- **Decision Graph & Replay** : Visualisation audit trail et rejeu de décisions
- **What-If Simulator** : Tests de scénarios avec sliders interactifs
- **Approvals Workflow** : Règle des deux personnes avec gouvernance par seuils
- **Canary/Progressive Delivery** : Auto-rollback sur violations SLO

### ✅ Analytics & Optimisation Avancées
- **OpenTelemetry Observability** : Tracing, métriques, export Prometheus
- **Feature Store** : Redis online + snapshots offline pour replay/backtesting
- **Traffic Optimizer v2** : Algorithmes Thompson Sampling et UCB bandits
- **Budget Arbitrage Optimizer** : Solveur OR-Tools LP/QP pour allocation optimale
- **Backtesting Engine** : Calcul uplift statistique et analyse contrefactuelle

### ✅ Intégrations Externes
- **Webhooks System** : Intégrations Slack, Jira, PagerDuty pour alertes

## 📁 Structure des Nouveaux Modules

```
src/soft/
├── pac/                    # Policy-as-Code
│   ├── models.py          # Modèles SQLAlchemy
│   ├── schemas.py         # Schémas Pydantic
│   ├── loader.py          # Chargeur/validateur YAML
│   ├── service.py         # Logique métier PaC
│   └── api.py             # Endpoints FastAPI
├── replay/                 # Decision Graph & Replay
│   ├── engine.py          # Moteur replay et what-if
│   └── api.py             # Endpoints replay
├── features/               # Feature Store
│   ├── service.py         # Service Redis + offline
│   └── api.py             # Endpoints features
├── autopilot/
│   ├── bandits/
│   │   └── thompson.py    # Thompson Sampling & UCB
│   └── planner/
│       └── optimizer.py   # Optimiseur OR-Tools
├── backtesting/            # Backtesting & Counterfactuals
│   ├── engine.py          # Moteur backtesting
│   └── api.py             # Endpoints backtesting
├── webhooks/               # Intégrations externes
│   ├── service.py         # Service webhooks
│   └── api.py             # Endpoints webhooks
└── observability/          # OpenTelemetry
    └── otel.py            # Setup observabilité
```

## 🚀 Instructions de Déploiement

### 1. Installation des Dépendances

```bash
# Installer les nouvelles dépendances
pip install aiohttp>=3.8.0
pip install ortools>=9.5.0
pip install opentelemetry-api>=1.20.0
pip install opentelemetry-sdk>=1.20.0
pip install opentelemetry-instrumentation-fastapi>=0.41b0
pip install opentelemetry-instrumentation-sqlalchemy>=0.41b0
pip install opentelemetry-exporter-prometheus>=0.57b0
pip install opentelemetry-exporter-otlp-proto-grpc>=1.20.0

# Ou utiliser le script fourni
.\install_new_deps.bat
```

### 2. Migration Base de Données

```bash
# Exécuter les migrations Alembic
alembic upgrade head
```

### 3. Configuration Redis (Optionnel)

```bash
# Installer Redis pour le Feature Store
# Windows : télécharger depuis https://redis.io/download
# Ou utiliser Redis Cloud/AWS ElastiCache en production
```

### 4. Variables d'Environnement

Ajouter au fichier `.env` :

```env
# Feature Store
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# OpenTelemetry (optionnel)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
GRAFANA_BASE_URL=http://localhost:3000

# Webhooks (optionnel)
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
JIRA_PROJECT_KEY=SMARTLINKS
PAGERDUTY_ROUTING_KEY=...
```

### 5. Test du Système

```bash
# Tester les imports RCP
python test_rcp_features.py

# Démarrer le serveur
python start_debug.py

# Vérifier les endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/docs
```

## 🔗 Nouveaux Endpoints API

### Policy-as-Code
- `POST /api/pac/validate` - Valider YAML PaC
- `POST /api/pac/plan` - Créer plan de déploiement
- `POST /api/pac/apply` - Appliquer plan
- `GET /api/pac/export` - Exporter politiques actuelles

### Replay & What-If
- `POST /api/replay/decision` - Rejouer décision
- `POST /api/replay/whatif` - Simulation what-if
- `POST /api/replay/shadow/enable` - Activer shadow run

### Feature Store
- `GET /api/features/online/{key}` - Récupérer feature online
- `POST /api/features/online/{key}` - Définir feature online
- `POST /api/features/snapshot` - Créer snapshot offline

### Bandits & Optimisation
- `POST /api/bandits/{algo_key}/optimize` - Optimiser trafic bandits
- `POST /api/optimizer/budget` - Optimiser allocation budget
- `POST /api/optimizer/weights` - Optimiser poids trafic

### Backtesting
- `POST /api/backtest/run` - Lancer backtesting
- `POST /api/backtest/counterfactual` - Analyse contrefactuelle

### Webhooks
- `POST /api/webhooks` - Enregistrer webhook
- `GET /api/webhooks` - Lister webhooks
- `POST /api/webhooks/test` - Tester webhook

## 🔒 Sécurité & RBAC

Tous les endpoints utilisent l'en-tête `X-Role` pour le contrôle d'accès :

- **viewer** : Lecture seule
- **operator** : Opérations courantes
- **admin** : Administration complète
- **dg_ai** : Privilèges maximaux

## 📊 Observabilité

### Métriques Prometheus
- `autopilot_actions_total` - Actions autopilot par état
- `rcp_evaluations_total` - Évaluations RCP
- `autopilot_run_duration_ms` - Durée exécution algorithmes
- `rcp_active_policies` - Nombre de politiques actives

### Dashboards Grafana
- Vue d'ensemble SmartLinks
- Métriques RCP détaillées
- Traces OpenTelemetry

## 🧪 Tests & Validation

```bash
# Tests unitaires
python -m pytest tests/

# Tests d'intégration RCP
python test_rcp_features.py

# Tests API
curl -X POST http://localhost:8000/api/pac/validate \
  -H "X-Role: admin" \
  -H "Content-Type: application/json" \
  -d '{"policies": []}'
```

## 🚨 Dépannage

### Problèmes Courants

1. **Erreur import OpenTelemetry**
   ```bash
   pip install opentelemetry-exporter-prometheus==0.57b0
   ```

2. **Redis non disponible**
   - Feature Store fonctionne en mode dégradé
   - Snapshots offline uniquement

3. **OR-Tools installation**
   ```bash
   pip install --upgrade ortools
   ```

### Logs de Debug

```bash
# Activer logs détaillés
export LOG_LEVEL=DEBUG
python start_debug.py
```

## 📈 Prochaines Étapes

1. **Tests d'intégration** complets avec données réelles
2. **Configuration production** avec Redis Cluster
3. **Monitoring avancé** avec Grafana/Prometheus
4. **Formation équipe** sur nouvelles fonctionnalités RCP
5. **Documentation API** complète avec exemples

---

🎉 **Le système RCP SmartLinks Autopilot est maintenant prêt pour le déploiement en production !**
