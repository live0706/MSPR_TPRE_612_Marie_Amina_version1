# Flux et notes de conformite

## Flux du pipeline (cartographie code)
1. Decouverte des sources : `etl/discover.py`
2. Extraction : `etl/extract.py`
3. Transformation et enrichissement : `etl/transform.py`
4. Qualite des donnees + metriques de modele : `etl/quality.py`, `etl/model.py`
5. Chargement PostgreSQL : `etl/load.py`
6. API : `api/main.py`, `api/routes.py`
7. Dashboard : `dashboard/app.py`

## Sources et outillage
- Sources decouvertes automatiquement via OpenDataSoft, completees par Wikipedia et sources statiques (ex: GTFS).
- Extraction compatible JSON, CSV, HTML et GTFS (.zip).
- Pipeline execute en bout en bout dans Docker et charge dans PostgreSQL.

## Suivi qualite et performance
- Rapport de qualite ecrit dans `data/processed/quality_report.json`
- Metriques de modele (regression lineaire simple CO2 vs distance) ecrites dans `data/processed/model_metrics.json`

## Correspondance avec road.txt (Bloc 1)
- Definir sources et outils : modules de decouverte + extraction, sources documentees.
- Recueillir l'information : sources heterogenes, persistance brute.
- Parametrer les imports : config JSON des sources, decouverte automatique.
- Analyser/nettoyer/trier : normalisation, gestion des manquants, enrichissement.
- Traiter les donnees : rapport qualite + metriques de modele predictif simple.
- Construire le stockage : schema SQL normalise + index.
- Exploiter/visualiser : API + dashboard.
