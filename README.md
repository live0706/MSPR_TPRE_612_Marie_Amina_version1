# ObRail Europe

Pipeline ETL complet pour les donnees ferroviaires europeennes : collecte, transformation, chargement dans PostgreSQL, exposition via API REST, et visualisation via un dashboard Streamlit.

## Fonctionnement (resume)
1. Decouverte des sources (`etl/discover.py`) -> generation de `etl/sources.json`
2. Extraction (HTML/CSV/JSON/GTFS) dans `data/raw`
3. Transformation (normalisation colonnes, conversion heures, filtrage `distance_km`, filtrage rail-only sur GTFS, calcul CO2)
4. Rapport de qualite + metriques de modele
5. Chargement PostgreSQL (`etl/load.py`)
6. API + dashboard

## Demarrage rapide (Docker)
1. Verifier le fichier `.env` (DATABASE_URL, DB_USER, DB_PASSWORD, DB_NAME).
2. Lancer la base :
   - `docker compose up -d db`
3. Executer l ETL :
   - `docker compose run --rm etl`
4. Lancer API et dashboard :
   - `docker compose up -d api dashboard`

## Demarrage local (sans Docker)
1. Definir l URL de la base :
   - ` $env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/obrail" `
2. Lancer l ETL :
   - `python .\etl\main_etl.py`

## Sources de donnees
- Back-on-Track (CSV) : actif, fournit horaires et distances.
- Wikipedia (HTML) : actif mais quasi filtre par `distance_km`.
- GTFS rail : supporte, a ajouter pour augmenter le volume.
- Transitland : supporte, peut exiger autorisation.

## Sorties
- Donnees brutes : `data/raw/`
- Rapports :
  - `data/processed/quality_report.json`
  - `data/processed/model_metrics.json`

## Structure du projet
- `etl/` : pipeline ETL
- `database/` : schema PostgreSQL
- `api/` : FastAPI
- `dashboard/` : Streamlit
- `docs/` : documentation (flow, api, mcd)

## Documentation
- Rapport detaille : `rapport-detaillé.md`
- Plan de soutenance : `presenttion.md`
- Flux ETL : `docs/flow.md`
- API : `docs/api.md`
- MCD : `docs/mcd.md`

## Tests
Aucun test automatise actif (supprimes pour le commit).
