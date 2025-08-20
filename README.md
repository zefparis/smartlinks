
# SmartLinks Autopilot — Soft local (no-UI)

> Un "soft" headless qui exécute l'algo d'orchestration: redirect minimal, anti-fraude légère, bandit basique, payout dynamique. Pas d'UI, pas de déploiement compliqué. Tu peux l'exécuter en local et (optionnel) exposer `/r` via ngrok/Tailscale.

## TL;DR
- Python 3.11+
- `pip install -r requirements.txt`
- Init DB + seed: `python -m soft.initdb`
- Lancer router HTTP: `python -m soft.router`
- Lancer autopilot (boucles payout/risk): `python -m soft.autopilot`
- Simuler du trafic/conversions: `python -m soft.simulate` (dev)

## Arbo
```
src/soft/
  __init__.py
  config.py
  storage.py
  router.py
  bandit.py
  fraud.py
  autopilot.py
  initdb.py
  simulate.py
policy.yaml
requirements.txt
.env.example
```

## Notes
- Base de données: SQLite `smartlinks.db` dans le dossier du projet (simplissime).
- En prod tu pourras swap pour ClickHouse/Redis; l'API des modules reste stable.
- Les endpoints exposés par `router.py` : `/r/{slug}` et `/postback`.
- Tout est codé en Python pur (pas de scikit-learn) pour éviter les installs lourdes.

## Exposition publique (optionnel)
- `ngrok http 8000` puis utilise l'URL publique pour les smartlinks.
- Ou Tailscale/Cloudflared si tu préfères.

## Stripe/Offres
- Place tes secrets dans `.env` (voir `.env.example`). Le code ne déclenche pas de paiement réel, il prépare des accruals; l'intégration Stripe Connect est un TODO volontaire.
