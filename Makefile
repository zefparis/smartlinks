# SmartLinks Autopilot - Makefile
# Commandes pour le développement et la gestion des données

.PHONY: help install seed-db seed-clean seed-high start-backend start-frontend start-all test clean

# Variables
PYTHON = .venv/Scripts/python.exe
PIP = .venv/Scripts/pip.exe

	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Installer les dépendances Python
	$(PIP) install -r requirements.txt
	@echo "Installing Node.js dependencies..."
	cd src/frontend && npm install

seed-db: ## Générer des données de test (30 jours, volume moyen)
	$(PYTHON) scripts/seed_database.py --days 30 --volume medium --force

seed-clean: ## Nettoyer et regénérer toutes les données
	$(PYTHON) scripts/seed_database.py --days 30 --volume medium --clean --force

seed-high: ## Générer un volume élevé de données (30 jours)
	$(PYTHON) scripts/seed_database.py --days 30 --volume high --clean --force

seed-week: ## Générer 7 jours de données
	$(PYTHON) scripts/seed_database.py --days 7 --volume medium --clean --force

seed-custom: ## Générer des données personnalisées (utiliser DAYS et VOLUME)
	$(PYTHON) scripts/seed_database.py --days $(or $(DAYS),30) --volume $(or $(VOLUME),medium) --clean --force

start-backend: ## Démarrer le backend FastAPI
	$(PYTHON) -m src.soft.router

start-frontend: ## Démarrer le frontend Vite (dans un autre terminal)
	cd src/frontend && npm run dev

start-all: ## Démarrer backend + frontend + IA supervisor
	start_all.bat

test: ## Lancer les tests
	$(PYTHON) -m pytest tests/ -v

test-db: ## Tester la connexion à la base de données
	$(PYTHON) -c "from src.soft.db import SessionLocal; from src.soft.models import Click; db = SessionLocal(); print(f'DB OK: {db.query(Click).count()} clics'); db.close()"

check-env: ## Vérifier l'environnement
	$(PYTHON) check_env.py

clean: ## Nettoyer les fichiers temporaires
	del /q *.pyc 2>nul || true
	rmdir /s /q __pycache__ 2>nul || true
	rmdir /s /q .pytest_cache 2>nul || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf src/frontend/dist 2>/dev/null || true
	rm -rf *.log 2>/dev/null || true

# Exemples d'utilisation:
# make seed-db          # Données standard
# make seed-high        # Volume élevé
# make seed-week        # 7 jours seulement
# make DAYS=60 VOLUME=high seed-custom  # 60 jours volume élevé
