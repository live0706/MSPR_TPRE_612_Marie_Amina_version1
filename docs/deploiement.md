# Deploiement

## Prerequis

- Docker Desktop ou Docker Engine avec Compose v2
- ports libres : `5432`, `8000`, `8501`, `9090`, `3000`

## Variables d'environnement

Copier puis adapter :

```bash
cp .env.example .env
```

Variables principales :

- `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DATABASE_URL`
- `APP_ENV`, `APP_VERSION`, `LOG_LEVEL`
- `ENABLE_PROMETHEUS`, `PROMETHEUS_URL`, `GRAFANA_URL`
- `APP_LOG_PATH`
- `CORS_ORIGINS`

## Lancer la plateforme

```bash
docker compose up -d --build
```

## Lancer l'ETL

```bash
docker compose run --rm etl
```

## Services exposes

- API : `http://localhost:8000`
- Swagger : `http://localhost:8000/api/docs`
- Dashboard : `http://localhost:8501`
- Prometheus : `http://localhost:9090`
- Grafana : `http://localhost:3000`

## Healthchecks

- API : `GET /health`
- Dashboard : `GET /`
- Base : `pg_isready`

## Conseils de soutenance

- lancer la stack avant la demo
- verifier `docker compose ps`
- verifier `GET /health`
- ouvrir Grafana, Swagger et le dashboard React en amont
- si Grafana a deja ete initialise, conserver le mot de passe defini dans son volume persistant
