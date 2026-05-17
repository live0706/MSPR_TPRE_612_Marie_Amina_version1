# Monitoring

## Stack retenue

- `Prometheus` pour la collecte des metriques
- `Blackbox Exporter` pour les probes HTTP
- `Grafana` pour la visualisation
- `Loki` pour le stockage des logs
- `Promtail` pour l'expedition des logs applicatifs

## Indicateurs suivis

- disponibilite de l'API via `probe_success`
- disponibilite de `/health`
- latence moyenne API
- debit HTTP
- taux d'erreurs 5xx
- sante du frontend React
- volumetrie metier exposee en metriques Prometheus natives
- fraicheur de la derniere ingestion
- resume de volumes et d'ingestion via `/api/monitoring/summary`

## Endpoints

- metriques Prometheus : `GET /metrics`
- sante : `GET /health`
- resume d'observabilite : `GET /api/monitoring/summary`
- readiness Loki : `GET http://localhost:3100/ready`

## Grafana

Le dashboard `ObRail Overview` est provisionne automatiquement depuis :

`monitoring/grafana/dashboards/obrail-overview.json`

Il presente notamment :

- disponibilite API / UI / base
- nombre total de trajets, pays et operateurs
- repartition jour / nuit
- latence moyenne
- debit HTTP
- taux d'erreurs
- requetes par endpoint
- fraicheur de l'ingestion
- logs applicatifs issus de Loki

Si Grafana a deja ete initialise une premiere fois, le mot de passe reel reste celui stocke dans son volume persistant, meme si `.env` change ensuite.

## Logs applicatifs

L'API ecrit les logs sur la sortie standard et dans `data/logs/api.log`.
`Promtail` lit ce fichier et l'envoie a `Loki`, ce qui permet leur consultation depuis Grafana.

Commandes utiles :

```bash
docker compose logs -f api
docker compose logs -f promtail
docker compose logs -f loki
docker compose logs -f dashboard
docker compose logs -f etl
```

## Metriques metier exposees

- `obrail_database_connected`
- `obrail_total_trips`
- `obrail_total_countries`
- `obrail_total_operators`
- `obrail_total_night_trips`
- `obrail_total_day_trips`
- `obrail_latest_ingestion_timestamp_seconds`

## Limites connues

- pas d'alerting Grafana active dans cette version
- pas de retention longue duree configuree pour Loki au-dela du stockage local du conteneur
