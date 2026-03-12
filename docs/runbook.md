# Runbook

## Demarrer la stack
```
docker compose up --build db api dashboard
```

## Lancer l'ETL
```
docker compose run --rm etl
```

## Checks de sante
- API : `GET /` doit renvoyer status ok
- Dashboard : ouvrir `http://localhost:8501`

## Problemes courants
Base pas prete :
- L'ETL peut partir avant Postgres. Relancer `docker compose run --rm etl`.

Dashboard vide :
- L'ETL n'a pas tourne ou n'a rien charge. Verifier les logs ETL et `data/raw`.

API ne se connecte pas a la BDD :
- Verifier `.env` et `DATABASE_URL`.
- Verifier que le conteneur Postgres tourne.

## Reinitialiser la base
Cela supprime les donnees et recree le schema :
```
docker compose down -v
docker compose up --build db
```
Puis relancer l'ETL.
