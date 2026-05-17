# Tests

## Strategie

- tests unitaires : validation des helpers frontend et des erreurs API
- tests d'integration : endpoints FastAPI avec PostgreSQL reel

## Commandes

Depuis l'hote :

```bash
pytest
```

Depuis Docker :

```bash
docker compose run --rm api pytest
```

Depuis le frontend React :

```bash
cd frontend
npm test
```

## Pre-requis pour les tests d'integration

- `DATABASE_URL` doit pointer vers une base PostgreSQL accessible
- le schema doit exister

Les tests d'integration inserent un petit jeu de donnees de test isole avec le prefixe `pytest_`.

## Couverture fonctionnelle

- `/health`
- `/trajets`
- `/trajets/{id}`
- `/stats/volumes`
- `/api/monitoring/summary`
- helpers React de formatage et d'aggregation

## Bonnes pratiques

- utiliser une base dediee aux tests
- ne pas lancer les tests d'integration sur une base de production
- conserver `pytest` dans la CI pour garantir la non-regression
