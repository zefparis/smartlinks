# 🏗️ SMARTLINKS AUTOPILOT - ARBORESCENCE COMPLÈTE

## 📁 Structure Principale

```
smartlinks-autopilot/
├── 📁 src/                           # Code source principal
│   ├── 📁 backend/                   # Backend FastAPI (nouveau)
│   │   ├── 📁 api/                   # Endpoints REST
│   │   ├── 📁 core/                  # Logique métier
│   │   └── main.py                   # Application principale
│   ├── 📁 frontend/                  # Frontend React/Vite
│   │   ├── 📁 src/                   # Code source React
│   │   │   ├── 📁 components/        # Composants réutilisables
│   │   │   ├── 📁 pages/             # Pages principales
│   │   │   │   ├── Analytics.tsx     # Dashboard analytics
│   │   │   │   └── Settings.tsx      # Configuration
│   │   │   ├── 📁 lib/               # Utilitaires
│   │   │   │   └── api.ts            # Client API
│   │   │   └── main.tsx              # Point d'entrée
│   │   ├── index.html                # Template HTML
│   │   ├── package.json              # Dépendances Node.js
│   │   └── vite.config.ts            # Configuration Vite
│   └── 📁 soft/                      # Backend actuel (legacy)
│       ├── 📁 api/                   # Routers FastAPI
│       │   ├── analytics_router.py   # Analytics endpoints
│       │   ├── settings_router.py    # Settings endpoints
│       │   ├── ai_dg_router.py       # AI DG endpoints
│       │   └── assistant_router.py   # Assistant endpoints
│       ├── 📁 dg/                    # Decision Generator (IA)
│       │   ├── 📁 ai/                # Intelligence artificielle
│       │   │   ├── supervisor.py     # IA Supervisor principal
│       │   │   ├── openai_factory.py # Factory OpenAI
│       │   │   └── openai_integration.py
│       │   ├── 📁 algorithms/        # Algorithmes autonomes
│       │   │   ├── 📁 optimization/  # Optimisation trafic/budget
│       │   │   ├── 📁 security/      # Sécurité et détection
│       │   │   ├── 📁 maintenance/   # Maintenance automatique
│       │   │   ├── 📁 monitoring/    # Surveillance système
│       │   │   └── 📁 simulation/    # Tests et simulations
│       │   ├── 📁 api/               # Endpoints IA
│       │   │   └── 📁 endpoints/     # Endpoints spécialisés
│       │   │       └── ia_supervisor.py
│       │   ├── 📁 core/              # Logique métier DG
│       │   ├── 📁 models/            # Modèles de décision
│       │   └── dependencies.py      # Injection dépendances
│       ├── 📁 models/                # Modèles SQLAlchemy
│       │   └── decision.py           # Modèles de décision
│       ├── router.py                 # Router principal
│       ├── models.py                 # Modèles DB principaux
│       ├── db.py                     # Configuration base de données
│       └── config.py                 # Configuration générale
├── 📁 scripts/                       # Scripts utilitaires
│   ├── cleanup.py                    # Nettoyage projet
│   ├── run_dev.py                    # Lancement développement
│   ├── seed_database.py              # Génération données
│   └── reset_database.py             # Reset base de données
├── 📁 tests/                         # Tests unitaires
│   ├── test_detailed.py              # Tests détaillés
│   ├── test_ia_supervisor.py         # Tests IA
│   └── test_predictive_alerting.py   # Tests alertes
├── 📁 docs/                          # Documentation
│   ├── algorithms.md                 # Documentation algorithmes
│   ├── ia_supervisor_api_reference.md
│   └── reporting_system.md
├── 📁 migrations/                    # Migrations base de données
├── 📁 static/                        # Fichiers statiques
├── .env                              # Variables d'environnement
├── .env.example                      # Exemple configuration
├── requirements.txt                  # Dépendances Python
├── package.json                      # Dépendances Node.js globales
├── Makefile                          # Scripts de développement
├── docker-compose.yml               # Configuration Docker
├── main.py                           # Point d'entrée backend
├── smartlinks.db                     # Base de données SQLite
└── README.md                         # Documentation principale
```

## 🎯 Composants Clés

### **Backend (FastAPI)**
- **Router Principal** : `src/soft/router.py`
- **Modèles DB** : `src/soft/models.py` (Click, Conversion, Offer, etc.)
- **Analytics** : `src/soft/api/analytics_router.py`
- **Settings** : `src/soft/api/settings_router.py`
- **IA Assistant** : `src/soft/api/assistant_router.py`

### **Frontend (React/TypeScript)**
- **Client API** : `src/frontend/src/lib/api.ts`
- **Dashboard** : `src/frontend/src/pages/Analytics.tsx`
- **Configuration** : `src/frontend/src/pages/Settings.tsx`

### **IA Decision Generator (DG)**
- **Superviseur IA** : `src/soft/dg/ai/supervisor.py`
- **Factory OpenAI** : `src/soft/dg/ai/openai_factory.py`
- **Algorithmes** : `src/soft/dg/algorithms/*/`
- **Endpoints IA** : `src/soft/dg/api/endpoints/ia_supervisor.py`

### **Base de Données**
- **SQLite** : `smartlinks.db` (développement)
- **Modèles** : Click, Conversion, Offer, Segment, Creator
- **Seed Data** : `seed_data.py`, `generate_data.py`

## 🔗 Endpoints API Principaux

### **Analytics** (`/api/analytics/`)
- `GET /devices` - Statistiques par appareil
- `GET /countries` - Statistiques par pays
- `GET /clicks/history` - Historique des clics
- `GET /health` - Santé du système

### **IA Supervisor** (`/api/ia/`)
- `POST /ask` - Questions à l'IA
- `GET /analyze` - Analyse système
- `POST /fix` - Correction automatique
- `GET /status` - Statut IA

### **Assistant** (`/api/assistant/`)
- `POST /ask` - Questions générales

### **Settings** (`/api/settings/`)
- `GET /` - Configuration complète
- `PUT /general` - Mise à jour générale
- `PUT /offer/{id}` - Configuration offre

## 🛠️ Scripts de Développement

### **Lancement**
```bash
python main.py                    # Backend seul
python scripts/run_dev.py         # Backend + Frontend
make dev                          # Via Makefile
```

### **Base de Données**
```bash
python seed_data.py               # Données de base
python generate_data.py           # Génération massive
python force_data_generation.py   # Reset + génération
```

### **Tests**
```bash
python -m pytest tests/           # Tests unitaires
python scripts/test_endpoints.py  # Tests intégration
```

## 📊 Fichiers de Configuration

- **`.env`** - Variables d'environnement (API keys, DB, etc.)
- **`requirements.txt`** - Dépendances Python
- **`package.json`** - Dépendances Node.js
- **`docker-compose.yml`** - Déploiement containerisé
- **`Makefile`** - Scripts de développement

## 🗄️ Base de Données (SQLite)

### **Tables Principales**
- **clicks** - Enregistrement des clics
- **conversions** - Conversions trackées
- **offers** - Offres disponibles
- **segments** - Segmentation trafic
- **creators** - Créateurs de contenu
- **payout_rates** - Taux de rémunération

### **Taille Actuelle**
- `smartlinks.db` : ~380KB (données de développement)
- `smartlinks.db-shm` : 32KB (shared memory)
- `smartlinks.db-wal` : 8KB (write-ahead log)

Cette structure combine un **backend FastAPI robuste**, un **frontend React moderne**, et un **système d'IA autonome** pour la prise de décision intelligente.
