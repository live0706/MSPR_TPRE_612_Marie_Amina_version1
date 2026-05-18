# CI/CD

## Pipeline GitHub Actions

Fichier : `.github/workflows/ci.yml`

## Etapes du pipeline

1. checkout du depot
2. installation de Python 3.11 et Node.js 20
3. installation du client PostgreSQL
4. installation des dependances backend et frontend
5. installation du navigateur `Chromium` pour `Playwright`
6. demarrage de PostgreSQL via `docker compose up -d db`
7. initialisation du schema PostgreSQL
8. execution de `pytest`
9. execution des tests frontend unitaires `npm test`
10. build du frontend React pour l'API reelle
11. creation des artefacts de sante requis par `/health`
12. seed de PostgreSQL via `database/seed_e2e.sql`
13. demarrage de l'API FastAPI reelle
14. execution des tests E2E `Playwright`
15. validation de `docker compose config`
16. export d'un `docker-compose.resolved.yml`
17. construction des images `api`, `dashboard` et `etl`
18. publication des artefacts testables et des rapports

## Artefacts publies

- `frontend-dist`
- `playwright-report`
- `docker-compose-resolved`

## Bonnes pratiques appliquees

- aucun secret commite
- variables passees par l'environnement CI
- utilisation d'une base PostgreSQL reelle dans la pipeline
- validation de la configuration Docker avant merge
- conservation d'un artefact frontend testable

## Evolutions possibles

- ajout d'un job de lint (`ruff`, `black --check`)
- publication des images sur un registry
- deploiement automatique en environnement de recette
