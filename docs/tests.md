# Tests

## Strategie

- tests unitaires backend : validation des erreurs, de la sante et des metriques
- tests d'integration backend : endpoints FastAPI avec PostgreSQL reel
- tests unitaires frontend : helpers de formatage et d'aggregation
- tests E2E frontend : parcours navigateur `Playwright` sur le dashboard React avec API et PostgreSQL reels

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
npm run build
npm run e2e
```

Depuis la stack Docker deja lancee :

```bash
docker compose up -d db api dashboard
psql -h localhost -U postgres -d obrail -f database/seed_e2e.sql
cd frontend
npm run e2e:stack
```

Pour une execution visuelle locale :

```bash
cd frontend
npm run e2e:headed
```

## Pre-requis pour les tests d'integration

- `DATABASE_URL` doit pointer vers une base PostgreSQL accessible
- le schema doit exister

Les tests d'integration inserent un petit jeu de donnees de test isole avec le prefixe `pytest_`.

## Pre-requis pour les tests E2E

- les dependances frontend doivent etre installees avec `npm ci` ou `npm install`
- le build du frontend doit etre disponible avant `npm run e2e`
- l'API doit etre disponible sur `http://127.0.0.1:8000`
- PostgreSQL doit etre seedee avec `database/seed_e2e.sql`
- la configuration CORS doit autoriser `http://127.0.0.1:4173`

## Couverture fonctionnelle

- `/health`
- `/metrics`
- `/trajets`
- `/trajets/{id}`
- `/stats/volumes`
- `/api/monitoring/summary`
- helpers React de formatage et d'aggregation
- chargement du dashboard React
- filtres principaux
- selection d'un trajet dans l'interface
- verification d'un parcours complet navigateur -> frontend -> API -> PostgreSQL

## Bonnes pratiques

- utiliser une base dediee aux tests
- ne pas lancer les tests d'integration sur une base de production
- conserver `pytest`, `npm test` et `npm run e2e` dans la CI pour garantir la non-regression
