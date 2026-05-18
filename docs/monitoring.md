# Monitoring

## Stack retenue

- `Prometheus` pour la collecte des metriques
- `Grafana` pour la visualisation et le pilotage des indicateurs
- logs applicatifs conserves dans `data/logs/api.log` et consultables aussi via `docker compose logs`

## Indicateurs suivis

- disponibilite de l'API via la metrique `up{job="obrail_api"}`
- etat global de `/health` via `obrail_api_healthy`
- etat PostgreSQL via `obrail_database_connected`
- disponibilite des artefacts ETL via `obrail_quality_report_available` et `obrail_model_metrics_available`
- latence moyenne API
- debit HTTP
- taux d'erreurs 5xx
- volumes metier exposes en metriques Prometheus natives
- fraicheur de la derniere ingestion
- resume de volumes et d'ingestion via `/api/monitoring/summary`

## Endpoints

- metriques Prometheus : `GET /metrics`
- sante : `GET /health`
- resume d'observabilite : `GET /api/monitoring/summary`

## Grafana

Le dashboard `ObRail Overview` est provisionne automatiquement depuis :

`monitoring/grafana/dashboards/obrail-overview.json`

Il presente notamment :

- disponibilite API et sante `/health`
- etat base PostgreSQL
- nombre total de trajets, pays et operateurs
- repartition jour / nuit
- disponibilite des artefacts ETL
- latence moyenne
- debit HTTP
- taux d'erreurs
- requetes par endpoint
- fraicheur de l'ingestion

Si Grafana a deja ete initialise une premiere fois, le mot de passe reel reste celui stocke dans son volume persistant, meme si `.env` change ensuite.

## Logs applicatifs

L'API ecrit les logs sur la sortie standard et dans `data/logs/api.log`.

Commandes utiles :

```bash
docker compose logs -f api
docker compose logs -f dashboard
docker compose logs -f prometheus
docker compose logs -f grafana
docker compose logs -f etl
```

## Metriques metier exposees

- `obrail_api_healthy`
- `obrail_database_connected`
- `obrail_quality_report_available`
- `obrail_model_metrics_available`
- `obrail_total_trips`
- `obrail_total_countries`
- `obrail_total_operators`
- `obrail_total_night_trips`
- `obrail_total_day_trips`
- `obrail_latest_ingestion_timestamp_seconds`

## Limites connues

- pas d'alerting Grafana active dans cette version
- pas de centralisation de logs dans Grafana dans cette version
