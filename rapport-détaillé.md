# Rapport detaille - Livrable ObRail Europe

## 0) Identite du livrable

Projet : ObRail Europe
Date : 2026-03-15
Depot GitHub : https://github.com/live0706/MSPR_TPRE_612_Marie_Amina_version1


## 1) Resume executif

Le projet met en place un pipeline ETL complet (collecte, nettoyage, transformation, chargement) alimente par des sources ouvertes, expose via une API REST et un dashboard. Les livrables techniques sont en place, avec un focus sur les trajets ferroviaires (filtrage rail uniquement) et une qualite de donnees renforcee par un filtrage sur `distance_km`.

## 2) Conformite aux livrables

1. Scripts ETL operationnels : OK
   - Scripts `etl/` operationnels, parametrables via `sources.json` et `DATABASE_URL`
2. MCD/MPD : Partiel
   - MCD textuel disponible (docs/mcd.md)
   - MPD conforme au schema `database/init.sql`
   - Diagramme graphique a produire si necessaire
3. Base de donnees relationnelle alimentee : Partiel
   - OK en Docker (via `DATABASE_URL` dans `.env`)
   - En local, `DATABASE_URL` doit etre defini
4. API REST fonctionnelle : OK
   - Endpoints `/`, `/trains`, `/stats`
5. Documentation technique complete : OK
   - Ce rapport + docs existants
6. Tableau de bord : OK
   - Streamlit + Plotly, KPIs et qualite
7. Support de soutenance : OK (plan detaille dans presenttion.md)

## 3) Correspondance avec les criteres (ETL)

- Definir les sources et outils : OK
  - Sources Open Data + outils Python (requests/pandas), PostgreSQL, FastAPI, Streamlit
- Recueillir les informations : OK
  - Extraction heterogene (HTML, CSV, GTFS)
- Parametrer les outils d'import : OK
  - `etl/sources_static.json` + `etl/discover.py`
- Analyser, nettoyer, trier : OK
  - Normalisation, nettoyage, filtrage `distance_km`, conversion dates/heures
- Traiter les donnees : Partiel
  - Rapport qualite et metriques modele
  - Pas de tests automatises actifs
- Construire la structure de stockage : OK
  - PostgreSQL, schema `trips`, contraintes `service_type`
- Exploiter et visualiser : OK
  - API + dashboard accessible

## 4) Correspondance avec les attentes du projet

- Collecte, recueil securise, parametrage : OK
- Qualite des donnees : OK
- Stockage (MCD/MPD) : Partiel (diagramme a completer)
- Visualisation : OK
- Exploitation : OK (requete API)
- Sources suggerees : Partiel
  - Back-on-Track : OK
  - Transitland : supporte, mais acces bloque par authentification (401)
  - Husahuc : a ajouter si necessaire

## 5) Architecture technique et stack

- ETL : Python (pandas, requests)
- Base : PostgreSQL
- API : FastAPI
- Dashboard : Streamlit + Plotly
- Orchestration : Docker Compose

## 6) Sources de donnees et justification

Sources actives via `etl/sources_static.json` :

1. Back-on-Track (Open Night Train DB, CSV)
   - Horaires, distance, operateur, couverture Europe
   - Donnees parfois incompletes ou marqueurs `#N/A`
2. Wikipedia (Named passenger trains of Europe, HTML)
   - Source stable, mais pas de distance fiable
   - Filtrage par `distance_km` elimine quasi toutes les lignes

Sources optionnelles :
- GTFS rail : supporte (filtre rail uniquement)
- Transitland : supporte mais requiert acces autorise
- Husahuc : a ajouter si disponibilite

## 7) Processus ETL (detail)

1. Decouverte des sources
   - `etl/discover.py` genere `etl/sources.json`
   - Ajoute automatiquement Wikipedia + sources statiques
2. Extraction
   - `etl/extract.py` telecharge et parse (HTML, CSV, GTFS)
   - Donnees brutes dans `data/raw`
3. Transformation
   - `etl/transform.py` normalise colonnes, nettoie `#N/A`, convertit heures
   - Filtre `distance_km` obligatoire
   - Filtre rail uniquement sur GTFS
   - Calcul CO2 si absent
4. Chargement
   - `etl/load.py` charge dans PostgreSQL via `DATABASE_URL`

## 8) Modele de donnees (MCD / MPD)

MCD (conceptuel) : voir docs/mcd.md

MPD (physique) : table `trips` (database/init.sql)
Champs :
- trip_id (PK)
- operator_name, origin_city, destination_city
- departure_time, arrival_time
- service_type (Jour/Nuit), train_type
- distance_km, co2_emissions
- source_origin, created_at

Contraintes et index :
- service_type controle (Jour/Nuit)
- index sur service_type, operator_name, origin_city

## 9) Base de donnees relationnelle

Execution Docker :
```
docker compose up -d db
docker compose run --rm etl
```

Execution locale :
```
$env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/obrail"
python .\\etl\\main_etl.py
```

## 10) API REST (spec et exemples)

Endpoints :
- `GET /` : health check
- `GET /trains?limit=20&offset=0&service_type=Jour|Nuit`
- `GET /stats`

Exemple :
`GET /trains?service_type=Nuit&limit=20&offset=0`

## 11) Dashboard

Fonctionnalites :
- KPIs : total trajets, trains de nuit, emission moyenne CO2, nb operateurs
- Graphiques : repartition Jour/Nuit, top operateurs
- Qualite : CO2 nuls ou manquants
- Table filtrable par operateur

## 12) Qualite des donnees (statistiques reelles)

Source : data/processed/quality_report.json (2026-03-12T14:46:25Z)

- total_rows : 352
- service_type : Jour 290, Nuit 62
- missing_rate_by_column : 0.0 sur toutes les colonnes
- co2_zero_or_missing : 0

## 13) Tests et validation

Tests automatises : non (supprimes pour le commit).
Validation :
- generation `quality_report.json`
- verification via dashboard

## 14) Limites et pistes d'amelioration

- Ajouter des feeds GTFS ferroviaires supplementaires
- Ajouter un diagramme MCD/MPD graphique
- Reintroduire des tests ETL/API
- Stabiliser Transitland (authentification)
