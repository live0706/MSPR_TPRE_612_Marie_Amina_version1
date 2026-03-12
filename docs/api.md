# API

URL de base : `http://localhost:8000`

## Endpoints
- `GET /` check de sante
- `GET /trains` liste des trains avec pagination et filtre optionnel
  - Parametres : `limit`, `offset`, `service_type` (Jour ou Nuit)
- `GET /stats` statistiques globales (comptages et part de nuit)

## Exemples
```
GET /trains?limit=20&offset=0&service_type=Nuit
GET /stats
```
