# CI/CD

## Pipeline GitHub Actions

Fichier : `.github/workflows/ci.yml`

## Etapes du pipeline

1. checkout du depot
2. installation de Python 3.11
3. installation du client PostgreSQL
4. installation des dependances `api`, `dashboard` legacy et `frontend`
5. initialisation du schema PostgreSQL
6. execution de `pytest`
7. execution des tests frontend `npm test`
8. validation de `docker compose config`
9. construction des images `api`, `dashboard` (frontend React) et `etl`

## Bonnes pratiques appliquees

- aucun secret commite
- variables passees par l'environnement CI
- utilisation d'un service PostgreSQL ephemere
- validation des images Docker avant merge

## Evolutions possibles

- ajout d'un job de lint (`ruff`, `black --check`)
- publication des images sur un registry
- deploiement automatique en environnement de recette
