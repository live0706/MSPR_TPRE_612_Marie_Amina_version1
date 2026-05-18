# Maintenance et rollback

## Maintenance courante

- verifier `docker compose ps`
- surveiller `GET /health`
- consulter les logs `docker compose logs -f`
- verifier `http://localhost:9090/api/v1/targets`
- rejouer l'ETL en cas de mise a jour source

## Sauvegarde

Exemple de dump PostgreSQL :

```bash
docker exec obrail_db pg_dump -U ${DB_USER} ${DB_NAME} > obrail_backup.sql
```

## Rollback applicatif

1. identifier la derniere image stable
2. rebasculer le tag Docker ou le commit Git
3. relancer :

```bash
docker compose up -d --build
```

## Rollback data

- restaurer le dump SQL si la base a ete corrompue
- rerun ETL si seule la couche metier doit etre regenee

## Incidents courants

- `health` en erreur : verifier la disponibilite PostgreSQL
- frontend vide : verifier que l'ETL a bien charge les donnees
- Grafana vide : verifier Prometheus et la presence des fichiers de provisioning
- logs absents ou insuffisants : verifier `data/logs/api.log` et `docker compose logs -f api`
