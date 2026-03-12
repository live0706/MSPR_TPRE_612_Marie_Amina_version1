# Architecture

## Composants
- Pipeline ETL (Python) dans `etl/`
- Base de donnees PostgreSQL dans `database/`
- API (FastAPI) dans `api/`
- Dashboard (Streamlit) dans `dashboard/`
- Orchestration via Docker Compose dans `docker-compose.yml`

## Flux de donnees
1. Decouverte des sources OpenDataSoft et Wikipedia
2. Extraction des donnees brutes dans `data/raw`
3. Transformation, nettoyage et enrichissement
4. Generation des rapports de qualite et metriques de modele dans `data/processed`
5. Chargement dans la table PostgreSQL `trips`
6. Exposition via l'API et visualisation dans le dashboard

## Services et ports
- Postgres : `localhost:5432`
- API : `localhost:8000`
- Dashboard : `localhost:8501`

## Interfaces principales
- L'ETL ecrit dans Postgres via `DATABASE_URL`
- L'API lit Postgres via `DATABASE_URL`
- Le dashboard lit Postgres via `DATABASE_URL`

## Configuration
La configuration principale est dans `.env` :
- `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `DATABASE_URL`
- `API_URL`
