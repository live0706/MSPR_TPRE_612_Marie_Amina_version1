# Conformite au cahier des charges MSPR TPRE532

Ce document fait le lien entre le sujet MSPR, la grille EPSI et l'etat reel du depot.

## 1. Backend

| Exigence | Etat | Implementation |
|---|---|---|
| `GET /trajets` | OK | `api/routers/journeys.py` |
| `GET /trajets/{id}` | OK | `api/routers/journeys.py` |
| `GET /stats/volumes` | OK | `api/routers/statistics.py` |
| `GET /health` | OK | `api/routers/health.py` |
| Gestion propre des erreurs HTTP | OK | `api/errors.py`, payload de validation homogenes |
| Validation Pydantic | OK | `api/schemas/` + validations `Query` / `Path` |
| Swagger / OpenAPI claire | OK | `api/main.py`, `docs_url=/api/docs` |
| Logs applicatifs | OK | `api/logging_config.py`, `data/logs/api.log` |
| Metriques Prometheus | OK | `api/main.py`, `api/metrics.py`, `/metrics` |
| Securisation basique des entrees | OK | filtres bornes, regex, SQL parametre, headers HTTP |

## 2. Frontend

| Exigence | Etat | Implementation |
|---|---|---|
| Interface professionnelle | OK | frontend React + Leaflet dans `frontend/src/` |
| Consulter les trajets | OK | carte + tableau `JourneyTable` |
| Filtrer / rechercher | OK | filtres pays, operateur, service, annee, recherche |
| Afficher des statistiques | OK | KPI, volumes, operateurs dominants |
| Voir l'etat de sante API | OK | badge et bloc monitoring |
| Afficher le monitoring | OK | liens Swagger / Prometheus / Grafana + resume |
| Ergonomie / accessibilite | PARTIEL | contrastes, focus, libelles clairs ; audit RGAA complet restant a faire |
| Tests frontend | OK | tests unitaires Node + E2E Playwright |

## 3. Docker / Production

| Exigence | Etat | Implementation |
|---|---|---|
| Dockerfile backend | OK | `api/Dockerfile` |
| Dockerfile frontend/dashboard | OK | `frontend/Dockerfile` |
| Dockerfile ETL | OK | `etl/Dockerfile` |
| `docker-compose.yml` complet | OK | DB, ETL, API, frontend, prometheus, grafana |
| Lancement `docker compose up -d --build` | OK | documente dans `README.md` et `docs/deploiement.md` |
| `.env.example` propre | OK | racine du depot |

## 4. Tests

| Exigence | Etat | Implementation |
|---|---|---|
| Tests unitaires backend | OK | `api/tests/` |
| Tests integration API + base | OK | `api/tests/conftest.py` + fixtures PostgreSQL |
| Tests frontend / E2E | OK | tests frontend Node + E2E Playwright |
| Commande claire | OK | `pytest`, `docker compose run --rm api pytest`, `cd frontend && npm test`, `npm run e2e` |

## 5. CI/CD

| Exigence | Etat | Implementation |
|---|---|---|
| GitHub Actions | OK | `.github/workflows/ci.yml` |
| Installation dependances | OK | Python + Node |
| Lancement tests | OK | `pytest` + `npm test` + `npm run e2e` |
| Qualite / validation compose | OK | `docker compose config` |
| Build des images Docker | OK | `docker compose build api dashboard etl` |
| Secrets non exposes | OK | variables d'environnement |

## 6. Monitoring / Observabilite

| Exigence | Etat | Implementation |
|---|---|---|
| Disponibilite API | OK | Prometheus `up{job="obrail_api"}` + Grafana |
| Endpoint `/health` | OK | metrique `obrail_api_healthy` + route dediee |
| Latence | OK | Prometheus `http_request_duration_seconds` |
| Taux d'erreurs | OK | `http_requests_total` par status |
| Logs applicatifs | OK | sortie standard Docker + `data/logs/api.log` |
| Volumes de donnees | OK | jauges `obrail_total_*` |
| Dashboard Grafana | OK | `monitoring/grafana/dashboards/obrail-overview.json` |

## 7. Documentation

| Exigence | Etat | Implementation |
|---|---|---|
| `README.md` complet | OK | racine du depot |
| `docs/architecture.md` | OK | present |
| `docs/deploiement.md` | OK | present |
| `docs/tests.md` | OK | present |
| `docs/cicd.md` | OK | present |
| `docs/monitoring.md` | OK | present |
| `docs/rgpd_accessibilite_securite.md` | OK | present |
| `docs/maintenance_rollback.md` | OK | present |
| Rapport technique | OK | `docs/rapport_mspr_tpre532.md` |
| Support / plan de soutenance | OK | `docs/soutenance_plan.md` |

## 8. Points de vigilance pour la soutenance

- l'accessibilite est traitee de facon pragmatique mais sans audit RGAA outille complet
- Grafana conserve le mot de passe de son volume persistant apres premiere initialisation
- la couverture historique `2015 -> aujourd'hui` depend encore des archives GTFS disponibles
- les E2E frontend utilisent un jeu de donnees seedee dedie pour rester stables sans perdre la chaine complete frontend -> API -> base

## 9. Conclusion

Le depot repond maintenant au coeur du cahier des charges TPRE532 :

- solution complete lancable en Docker Compose
- backend FastAPI stabilise et documente
- frontend React demonstrable et plus presentable
- ETL integre a une architecture exploitable
- tests automatises
- CI/CD
- supervision Prometheus et Grafana
- documentation de production et de soutenance

Les ecarts restants sont des pistes d'amelioration, pas des blocages pour la remise MSPR.
