# Installation

## Prerequis
- Docker et Docker Compose
- Python 3.11 si execution sans Docker

## Lancer avec Docker
1. Verifier les valeurs de `.env`.
2. Demarrer la base, l'API et le dashboard :
```
docker compose up --build db api dashboard
```
3. Lancer l'ETL une fois :
```
docker compose run --rm etl
```

## Sources GTFS et Transitland
- Transitland est active par defaut via `etl/discover.py` (API REST).
- Variables utiles :
  - `TRANSITLAND_ENABLED` (true/false)
  - `TRANSITLAND_MAX_FEEDS` (0 = illimite)
  - `TRANSITLAND_PER_PAGE` (defaut 500)
  - `TRANSITLAND_REST_URL` (defaut https://transit.land/api/v2/rest/feeds)
- Sources statiques locales : editer `etl/sources_static.json` pour ajouter des URLs GTFS ou CSV.

## Lancer sans Docker
1. Creer et activer un environnement virtuel Python.
2. Installer les dependances :
```
pip install -r etl/requirements.txt
pip install -r api/requirements.txt
pip install -r dashboard/requirements.txt
```
3. Demarrer Postgres et creer le schema :
```
psql "$DATABASE_URL" -f database/init.sql
```
4. Lancer l'ETL :
```
python etl/main_etl.py
```
5. Lancer l'API :
```
uvicorn api.main:app --reload
```
6. Lancer le dashboard :
```
streamlit run dashboard/app.py
```
