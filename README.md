# ObRail Europe

End-to-end pipeline that discovers European rail datasets, extracts and cleans them, loads them into PostgreSQL, exposes an API, and renders a Streamlit dashboard.

## Flow (high level)
1. Discover sources (OpenDataSoft catalog + Wikipedia)
2. Extract raw data (JSON/CSV/HTML)
3. Transform, normalize, and enrich
4. Data quality report + simple CO2 model metrics
5. Load to PostgreSQL
6. API + dashboard

More detail and compliance notes: `docs/flow.md`.

## Quick start (Docker)
1. Ensure `.env` is set (see `.env` in repo root).
2. Start DB, API, and dashboard:
   - `docker compose up --build db api dashboard`
3. Run ETL once:
   - `docker compose run --rm etl`

## Outputs
- Raw data: `data/raw/`
- Processed metrics:
  - `data/processed/quality_report.json`
  - `data/processed/model_metrics.json`

## Data path
ETL uses `DATA_DIR` if defined; default is `../data` from the ETL folder. In Docker, `DATA_DIR` is set to `/app/data` via `docker-compose.yml`.

## Tests
Run with `pytest`. The suite covers ETL transforms/quality/model metrics and API endpoints using SQLite.

## API (summary)
See `docs/api.md`.
