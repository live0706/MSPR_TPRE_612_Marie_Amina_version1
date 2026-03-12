# Donnees

## Sources
- Decouverte via le catalogue OpenDataSoft (donnees ferroviaires europeennes)
- Liste Wikipedia des trains de voyageurs nommes

## Organisation des donnees
- Fichiers bruts : `data/raw`
- Artifacts traites :
  - `data/processed/quality_report.json`
  - `data/processed/model_metrics.json`

## Schema de base de donnees
Table : `trips`

Colonnes :
- `trip_id` (PK)
- `operator_name`
- `origin_city`
- `destination_city`
- `departure_time`
- `arrival_time`
- `service_type` (Jour ou Nuit)
- `train_type`
- `distance_km`
- `co2_emissions`
- `source_origin`
- `created_at`

## Rapport de qualite
`quality_report.json` contient :
- nombre total de lignes
- taux de valeurs manquantes par colonne
- nombre de doublons de `trip_id`
- repartition `service_type`
- nombre de valeurs CO2 a zero ou manquantes

## Rapport de metriques de modele
`model_metrics.json` contient :
- coefficients d'une regression lineaire simple (CO2 vs distance)
- MAE, RMSE et R2

## Sources statiques additionnelles
Le fichier `etl/sources_static.json` permet d'ajouter des sources (ex: GTFS .zip).
