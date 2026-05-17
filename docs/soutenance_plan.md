# Plan de soutenance

## Slide 1 - Contexte

- MSPR EPSI TPRE532
- besoin : industrialiser le prototype ObRail

## Slide 2 - Probleme initial

- ETL present mais peu industrialise
- API sans tests ni monitoring complet
- dashboard utile mais peu exploitable en production

## Slide 3 - Architecture cible

- ETL batch
- PostgreSQL
- FastAPI
- React + Leaflet
- Prometheus / Grafana / Blackbox

## Slide 4 - Evolutions backend

- endpoints normalises
- validation et gestion d'erreurs
- Swagger
- logs et metriques

## Slide 5 - Evolutions frontend

- consultation des trajets
- filtres et statistiques
- page monitoring

## Slide 6 - Docker et exploitation

- `docker compose up -d --build`
- healthchecks
- variables d'environnement

## Slide 7 - Tests et CI/CD

- pytest unitaires et integration
- GitHub Actions
- build des images

## Slide 8 - Monitoring

- Prometheus
- Blackbox Exporter
- Grafana

## Slide 9 - Securite / RGPD / accessibilite

- pas de donnees personnelles
- validation des entrees
- CORS et secrets hors depot

## Slide 10 - Conclusion

- prototype transforme en socle deployable
- plateforme demonstrable devant jury
- pistes futures : auth, reverse proxy, centralisation logs
