# 🤖 IA Supervisor - SmartLinks DG

## 🎯 Vue d'ensemble

L'IA Supervisor est un module intelligent intégré au backend SmartLinks DG qui fournit des capacités d'analyse, de diagnostic et de prise de décision automatisée via OpenAI GPT-4o (avec support O3 High Reasoning).

## ✨ Fonctionnalités principales

- **🧠 Intelligence artificielle** : Analyse système via GPT-4o/O3
- **🔧 Mode dégradé** : Fonctionnement sans OpenAI si indisponible
- **🛡️ Gestion d'erreurs robuste** : Timeouts, retry, fallbacks
- **🏭 Factory pattern** : Client OpenAI singleton avec DI
- **📊 Selfcheck complet** : Diagnostic automatique de santé
- **🎮 Modes d'opération** : Auto, Manual, Sandbox
- **🔌 Plug & Play** : Intégration transparente FastAPI

## 🚀 Installation rapide

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Configurer OpenAI
cp .env.example .env
# Éditer .env avec votre clé OPENAI_API_KEY

# 3. Démarrer le serveur
python main.py

# 4. Tester l'installation
curl http://localhost:8000/api/ia/selfcheck
```

## 📡 Endpoints disponibles

| Endpoint | Description |
|----------|-------------|
| `POST /api/ia/ask` | Poser une question à l'IA |
| `GET /api/ia/analyze` | Analyser l'état système |
| `POST /api/ia/fix` | Corriger les issues |
| `GET /api/ia/status` | Statut du supervisor |
| `GET /api/ia/selfcheck` | Diagnostic complet |
| `POST /api/ia/switch-mode` | Changer le mode |

## 🛠️ Architecture

```
src/soft/dg/ai/
├── openai_factory.py     # 🏭 Factory OpenAI + gestion erreurs
├── supervisor.py         # 🧠 Logique métier IA Supervisor  
└── openai_integration.py # 📜 Legacy (à supprimer)

src/soft/dg/api/
├── endpoints/
│   └── ia_supervisor_v2.py # 🌐 Endpoints FastAPI robustes
└── router.py               # 🔗 Router principal
```

## 🎮 Modes d'opération

- **AUTO** 🤖 : Exécution automatique des actions
- **MANUAL** 👤 : Approbation humaine requise
- **SANDBOX** 🧪 : Simulation sans exécution réelle

## 🔧 Configuration

### Variables d'environnement (.env)
```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
OPENAI_API_BASE=

# Support O3 High Reasoning (quand disponible)
# OPENAI_MODEL=o3-high-reasoning
```

## 📋 Exemples d'utilisation

### Question à l'IA
```bash
curl -X POST "http://localhost:8000/api/ia/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Quel est l'\''état du système?"}'
```

### Analyse système
```bash
curl "http://localhost:8000/api/ia/analyze"
```

### Mode sandbox
```bash
curl -X POST "http://localhost:8000/api/ia/switch-mode" \
  -H "Content-Type: application/json" \
  -d '{"mode": "sandbox"}'
```

## 🛡️ Mode dégradé

Si OpenAI est indisponible :
- ✅ Le système continue de fonctionner
- ⚠️ Réponses par défaut pour les questions IA
- 📊 Analyses basiques sans intelligence artificielle
- 🔄 Retry automatique en arrière-plan

## 🧪 Tests et validation

```bash
# Selfcheck complet
curl http://localhost:8000/api/ia/selfcheck

# Health check simple  
curl http://localhost:8000/api/ia/health

# Logs d'interaction
curl http://localhost:8000/api/ia/logs?limit=10
```

## 📚 Documentation complète

- [📖 Guide d'installation](docs/ia_supervisor_installation.md)
- [🔧 Référence API](docs/ia_supervisor_api_reference.md)

## 🔒 Sécurité

- ⚠️ **Jamais** de clé API dans le code
- 🔐 Configuration via `.env` uniquement
- 🛡️ Validation des entrées utilisateur
- 📊 Monitoring des usages OpenAI

## 🚨 Troubleshooting

### Erreur "OpenAI API key not found"
```bash
# Vérifier la configuration
grep OPENAI_API_KEY .env
```

### Mode dégradé persistant
```bash
# Vérifier les logs
tail -f autopilot.log | grep "OpenAI\|IASupervisor"
```

### Rate limit OpenAI
- ⏱️ Retry automatique intégré
- 📊 Surveillez votre usage via dashboard OpenAI

## 🎯 Roadmap

- [ ] Cache des réponses IA
- [ ] Métriques Prometheus
- [ ] Support streaming responses
- [ ] Interface web d'administration
- [ ] Intégration webhooks

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature
3. Tester avec `python -m pytest tests/`
4. Soumettre une PR

## 📄 Licence

Projet SmartLinks DG - Usage interne

---

**🎉 L'IA Supervisor est maintenant prêt ! Testez avec `/api/ia/selfcheck` pour valider l'installation.**
