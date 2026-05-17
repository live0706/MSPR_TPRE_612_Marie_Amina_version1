# ObRail Europe - MSPR TPRE532

ObRail Europe est une solution de data engineering et de restitution ferroviaire europeenne industrialisee pour la MSPR EPSI TPRE532. Le projet assemble un ETL Python, une API FastAPI, une base PostgreSQL, un frontend React cartographique et une couche d'observabilite Prometheus/Grafana.

## Objectifs

- consolider des donnees ferroviaires europeennes dans PostgreSQL
- exposer une API documentee et testee
- fournir une interface de consultation des trajets et des statistiques
- superviser l'etat de la plateforme
- fournir un socle Docker, CI/CD, documentation et runbooks

## Services

- `db` : PostgreSQL 15
- `etl` : pipeline batch d'extraction / transformation / chargement
- `api` : FastAPI sur `http://localhost:8000`
- `dashboard` : frontend React cartographique sur `http://localhost:8501`
- `prometheus` : supervision metrics sur `http://localhost:9090`
- `grafana` : dashboards sur `http://localhost:3000`
- `loki` : centralisation des logs sur `http://localhost:3100`
- `promtail` : collecte des logs applicatifs vers Loki
- `blackbox` : probes HTTP pour `/health`

## Endpoints principaux

- `GET /health`
- `GET /trajets`
- `GET /trajets/{id}`
- `GET /stats/volumes`
- `GET /api/docs`
- `GET /api/monitoring/summary`
- `GET /metrics`

## Lancement rapide

1. Copier la configuration d'environnement :

```bash
cp .env.example .env
```

2. Demarrer la stack :

```bash
docker compose up -d --build
```

3. Lancer un chargement ETL si necessaire :

```bash
docker compose run --rm etl
```

## Tests

Tests Python :

```bash
pytest
```

Tests frontend :

```bash
cd frontend
npm test
```

Tests dans le conteneur API :

```bash
docker compose run --rm api pytest
```

## Documentation

- [Architecture](docs/architecture.md)
- [Deploiement](docs/deploiement.md)
- [Tests](docs/tests.md)
- [CI/CD](docs/cicd.md)
- [Monitoring](docs/monitoring.md)
- [Conformite cahier des charges](docs/conformite_mspr_tpre532.md)
- [RGPD, accessibilite, securite](docs/rgpd_accessibilite_securite.md)
- [Maintenance et rollback](docs/maintenance_rollback.md)
- [Plan de soutenance](docs/soutenance_plan.md)

## Structure cible

```text
.
|-- api/
|-- dashboard/
|-- frontend/
|-- database/
|-- etl/
|-- monitoring/
|-- docs/
|-- .github/workflows/ci.yml
|-- docker-compose.yml
`-- README.md
```

## Remarques MSPR

- l'ETL est conserve en batch pour ne pas coupler la collecte au runtime de l'API
- le frontend React fournit une experience plus presentable pour la soutenance, avec carte interactive, filtres et monitoring
- Prometheus, Blackbox, Loki et Grafana couvrent la disponibilite, la latence, le taux d'erreur, la sante HTTP et les logs applicatifs
