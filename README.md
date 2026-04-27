# ObRail Europe - MSPR TPRE 612

## Objectif de ce depot

Ce projet contient une premiere version fonctionnelle de la plateforme ObRail Europe :

- un ETL Python ;
- une base PostgreSQL ;
- une API FastAPI ;
- un dashboard Streamlit ;
- une orchestration Docker Compose.

Le travail a faire maintenant consiste a faire evoluer ce depot en s'appuyant sur le projet de reference :

- `../MSPR_1_B3-main/MSPR_1_B3-main/`

Le but n'est pas de recopier aveuglement le projet de reference, mais de comprendre ce qu'il apporte, ce qui manque ici, puis d'aligner progressivement `MSPR_TPRE_612_Marie_Amina_version1` sur cette architecture.

---

## Mise a jour de l'etat du projet

Une premiere vague d'alignement a deja ete faite dans ce depot.

### Ce qui est maintenant en place

- un schema analytique ajoute dans `database/init.sql` :
  - `dim_countries`
  - `dim_years`
  - `dim_operators`
  - `facts_night_trains`
  - `facts_country_stats`
  - `dashboard_metrics`
- une migration additive `database/02_add_analytics.sql` pour les bases Docker deja existantes
- un ETL qui :
  - sauvegarde `data/processed/trips_cleaned_final.csv`
  - charge la couche transactionnelle
  - charge aussi la couche analytique
- une API modulaire dans `api/routers/`
- des schemas Pydantic par domaine dans `api/schemas/`
- un dashboard principal qui interroge l'API
- un `dashboard/app_ai.py` pour visualiser qualite et metriques du modele
- un `docker-compose.yml` coherent avec ces composants

### Ce qu'il reste encore a fiabiliser ou enrichir

- ameliorer les vraies sources metier dans `etl/sources.json`
- affiner l'inference pays pour les flux GTFS heterogenes
- ajouter de vrais tests fonctionnels API / ETL / dashboard
- lancer un test complet Docker sur machine cible apres reconstruction des images

### Important pour la lecture de ce README

Les sections d'analyse plus bas conservent volontairement :

- le diagnostic initial ;
- la comparaison avec `MSPR_1_B3-main` ;
- l'ordre logique des travaux.

Donc :

- le haut du README decrit l'etat actuel apres les premieres modifications ;
- le bas du README explique pourquoi ces modifications ont ete necessaires et ce qu'il reste a faire.

---

## Lecture rapide

Si tu veux comprendre le depot sans te perdre, lis dans cet ordre :

1. `docker-compose.yml`
2. `database/init.sql`
3. `database/02_add_analytics.sql`
4. `etl/main_etl.py`
5. `etl/load.py`
6. `api/main.py`
7. `api/routers/`
8. `api/routes.py`
9. `dashboard/app.py`
10. `dashboard/app_ai.py`

Puis lis les sections `Ecarts avec MSPR_1_B3-main` et `Plan de modification recommande` plus bas pour comprendre le pourquoi.

---

## Diagnostic initial du projet cible

### 1. Architecture actuelle

Le depot `MSPR_TPRE_612_Marie_Amina_version1` est organise ainsi :

```text
MSPR_TPRE_612_Marie_Amina_version1/
|-- docker-compose.yml
|-- README.md
|-- api/
|   |-- main.py
|   |-- routes.py
|   |-- database.py
|   |-- utils.py
|   |-- routers/
|   |   |-- analysis.py
|   |   |-- countries.py
|   |   |-- dashboard.py
|   |   |-- metadata.py
|   |   |-- operators.py
|   |   |-- statistics.py
|   |   `-- trains.py
|   |-- schemas/
|   |   |-- countries.py
|   |   |-- operators.py
|   |   |-- statistics.py
|   |   `-- trains.py
|   |-- Dockerfile
|   `-- requirements.txt
|-- dashboard/
|   |-- app.py
|   |-- app_ai.py
|   |-- Dockerfile
|   `-- requirements.txt
|-- database/
|   |-- init.sql
|   `-- models.py
`-- etl/
    |-- main_etl.py
    |-- extract.py
    |-- transform.py
    |-- load.py
    |-- quality.py
    |-- model.py
    |-- gtfs.py
    |-- discover.py
    |-- sources.json
    |-- Dockerfile
    `-- requirements.txt
```

### 2. Ce que fait cette version

Le pipeline actuel suit cette logique :

1. lecture de `etl/sources.json` ;
2. telechargement de sources heterogenes via `etl/extract.py` ;
3. parsing CSV / JSON / HTML / GTFS ;
4. normalisation dans `etl/transform.py` ;
5. calcul simple des emissions CO2 ;
6. generation d'un rapport qualite JSON ;
7. generation d'un fichier de metriques de modele ;
8. chargement en base dans les tables transactionnelles ;
9. exposition minimale via une API ;
10. affichage via un dashboard connecte directement a la base.

### 3. Schema de donnees actuel

Le schema actuel de `database/init.sql` est oriente "ingestion / parcours" :

- `sources`
- `ingestions`
- `operators`
- `stations`
- `routes`
- `trips`

Ce schema est utile pour tracer l'origine des trajets, mais il ne correspond pas au schema analytique du projet de reference.

### 4. API actuelle

L'API actuelle expose seulement deux endpoints dans `api/routes.py` :

- `GET /trains`
- `GET /stats`

Elle est simple, mais trop limitee pour alimenter un dashboard analytique riche.

### 5. Dashboard actuel

Le dashboard actuel dans `dashboard/app.py` :

- interroge directement PostgreSQL ;
- n'utilise pas l'API ;
- affiche quelques KPI simples ;
- n'a pas la structure multi-pages du projet de reference.

### 6. Qualite et modelisation actuelle

Le projet genere deja :

- `data/processed/quality_report.json`
- `data/processed/model_metrics.json`

Mais :

- l'API ne les expose pas ;
- le dashboard ne les consomme pas ;
- la structure de rapport est beaucoup plus simple que dans le projet de reference.

---

## Ce que contient MSPR_1_B3-main

Le projet `MSPR_1_B3-main` est plus proche d'une plateforme analytique complete.

### 1. ETL plus structure

Le projet de reference separe clairement :

- `etl/extract/`
- `etl/transform/`
- `etl/load/`

Il produit aussi :

- `data/raw/`
- `data/processed/`
- `data/warehouse/`
- des rapports de qualite detailles ;
- des fichiers de traceabilite ;
- un chargement structure vers un schema analytique.

### 2. Schema analytique en etoile

Le schema SQL du projet de reference repose sur :

- `dim_countries`
- `dim_years`
- `dim_operators`
- `facts_night_trains`
- `facts_country_stats`
- la vue `dashboard_metrics`

Ce schema est adapte a l'analyse, au filtrage par annee/pays/operateur, et au dashboard.

### 3. API modulaire

L'API de reference est decoupee en routeurs :

- `countries`
- `night_trains`
- `dashboard`
- `analysis`
- `operators`
- `metadata`
- `statistics`

Elle expose plusieurs familles d'endpoints :

- liste des pays ;
- statistiques par pays ;
- trains jour / nuit ;
- KPI dashboard ;
- classements CO2 ;
- timeline ;
- recommandations ;
- metadonnees et qualite ;
- couverture geographique.

### 4. Dashboard branche sur l'API

Le dashboard de reference :

- ne parle pas directement a la base ;
- consomme l'API ;
- gere des filtres globaux ;
- affiche plusieurs vues d'analyse ;
- s'appuie sur les endpoints analytiques de l'API.

### 5. Documentation et tests

Le projet de reference contient en plus :

- un README plus structure ;
- une documentation technique dans `docs/` ;
- un test API (`platform/server/test/test_api.py`) ;
- un rapport qualite expose via l'API.

---

## Ecarts avec MSPR_1_B3-main

La comparaison ci-dessous est le point cle pour savoir quoi modifier.

| Sujet | MSPR_1_B3-main | MSPR_TPRE_612_Marie_Amina_version1 | Ecart |
|---|---|---|---|
| Architecture ETL | dossiers `extract/`, `transform/`, `load/` | gros modules uniques `extract.py`, `transform.py`, `load.py` | le projet cible est plus compact mais moins modulaire |
| Schema BDD | schema analytique `dim_*` + `facts_*` + vue | schema transactionnel `sources/stations/routes/trips` | la base cible ne porte pas les analyses attendues |
| KPI pays / annees | oui | non | il manque la couche analytique par pays et par annee |
| Distinction jour / nuit | `is_night` explicite + endpoints dedies | `service_type` calcule et simple filtre `/trains` | logique moins robuste et moins exploitable |
| API | modulaire et riche | 2 endpoints seulement | gros manque fonctionnel |
| Dashboard | multi-pages via API | dashboard simple via SQL direct | couplage fort a la base et capacites limitees |
| Qualite / metadata | exposees par API | fichiers JSON seulement | manque de transparence cote API/dashboard |
| Tests | presence d'un fichier de tests API | aucun test repere | manque de verification |
| Documentation | README + docs techniques | README minimal et references vers docs absents | documentation a reprendre |

---

## Ce qui manque concretement dans le projet cible

### 1. Il manque un schema analytique exploitable

Le point principal est la base. Le projet cible stocke des trajets, mais pas de vraies dimensions analytiques.

Ce qui manque :

- une dimension pays ;
- une dimension annee ;
- une dimension operateurs propre a l'analyse ;
- une table de faits pour les trains jour/nuit ;
- une table de faits pour les statistiques pays ;
- une vue ou une table agregée pour le dashboard.

Sans cela, on ne peut pas reproduire proprement les endpoints ni les graphiques du projet de reference.

### 2. Il manque les sources metier du projet de reference

Le projet de reference exploite de vraies sources d'analyse europeennes :

- Eurostat ;
- Back-on-Track ;
- GTFS FR / CH / DE ;
- emissions CO2.

Dans le projet cible, `etl/sources.json` est aujourd'hui centre sur :

- Wikipedia ;
- de tres nombreux flux GTFS PAN ;
- plusieurs jeux de donnees qui ne sont pas strictement ferroviaires.

Ce qui manque donc ici n'est pas seulement du code : il manque aussi la bonne selection de sources.

### 3. Il manque une vraie couche de transformation analytique

Le `transform.py` actuel nettoie et filtre des trajets, mais il ne produit pas :

- un referentiel pays standardise ;
- une consolidation par annee ;
- des faits pays ;
- une table de trains analytiques de type `facts_night_trains` ;
- une preparation de `data/warehouse/`.

### 4. Il manque une API exploitable par un dashboard avance

L'API actuelle ne propose pas :

- `GET /api/countries`
- `GET /api/countries/stats`
- `GET /api/night-trains`
- `GET /api/night-trains/night`
- `GET /api/night-trains/day`
- `GET /api/dashboard/metrics`
- `GET /api/dashboard/kpis`
- `GET /api/statistics/timeline`
- `GET /api/statistics/co2-ranking`
- `GET /api/analysis/train-types-comparison`
- `GET /api/analysis/policy-recommendations`
- `GET /api/operators`
- `GET /api/operators/{operator_id}/stats`
- `GET /api/metadata/quality`
- `GET /api/metadata/sources`
- `GET /api/geographic/coverage`

### 5. Il manque l'alignement dashboard <-> API

Le dashboard de reference consomme l'API. Le dashboard cible, lui, requete la base directement.

Ce qu'il faut changer :

- faire passer le dashboard par l'API ;
- centraliser les regles metier dans l'API ;
- reduire le couplage du dashboard avec PostgreSQL.

### 6. Il manque des tests

Le projet de reference essaie au moins de couvrir ses endpoints. Le projet cible n'a pas de tests detectes.

### 7. Il manque de la coherence documentaire

Le README precedent faisait reference a :

- `docs/flow.md`
- `docs/api.md`
- `docs/mcd.md`
- `rapport-detaille.md`
- `presenttion.md`

Ces fichiers n'ont pas ete retrouves dans le depot cible. Il fallait donc nettoyer et reconstruire la documentation.

---

## Incoherences initiales detectees dans le projet cible

Ces points ne sont pas juste des "manques" par rapport a la reference. Ce sont aussi des sujets a corriger dans le depot cible lui-meme.

### 1. Service Docker `dashboard_ai` incomplet

Dans `docker-compose.yml`, le service `dashboard_ai` lance :

- `streamlit run app_ai.py`

Or le fichier `dashboard/app_ai.py` n'est pas present dans le depot.

Conclusion :

- soit on supprime temporairement ce service ;
- soit on cree la page IA ensuite.

### 2. `etl/discover.py` existe mais n'est pas branche au pipeline principal

Le module de decouverte automatique existe, mais `etl/main_etl.py` ne s'en sert pas directement.

Conclusion :

- soit on l'assume comme outil auxiliaire ;
- soit on l'integre clairement au flux ETL.

### 3. Le chargement actuel force `stations.country = "Unknown"`

Dans `etl/load.py`, les gares sont chargees avec un pays par defaut `"Unknown"`.

Conclusion :

- on perd une information cle pour l'analyse par pays ;
- cela bloque une partie du futur dashboard analytique.

### 4. Les rapports qualite / modele ne sont pas relies a l'application

Le pipeline genere des JSON utiles, mais ils ne sont ni exposes par l'API ni exploites dans le dashboard courant.

---

## Strategie recommandee

La meilleure approche est de conserver les bonnes idees du projet cible, puis d'y greffer l'architecture analytique du projet de reference.

### Ce qu'on garde du projet cible

- la base d'ingestion `sources` / `ingestions` ;
- la logique de telechargement generique ;
- la structure Docker simple ;
- le dashboard Streamlit comme interface finale ;
- la production de rapports JSON.

### Ce qu'on reprend du projet de reference

- le schema analytique `dim_*` / `facts_*` ;
- l'API modulaire par routeur ;
- la logique de KPI et de statistiques ;
- l'organisation du dashboard autour de l'API ;
- la documentation plus nette ;
- les tests d'API.

### Decision technique recommande

Recommendation :

1. ne pas supprimer tout de suite le schema actuel `sources/stations/routes/trips` ;
2. ajouter en plus une couche analytique proche de `MSPR_1_B3-main` ;
3. faire evoluer ensuite l'API et le dashboard pour lire cette couche analytique ;
4. garder les tables d'ingestion pour la tracabilite.

Autrement dit :

- schema actuel = couche de collecte et de tracabilite ;
- nouveau schema analytique = couche de restitution.

---

## Plan de modification recommande

Voici l'ordre de travail conseille pour ne pas casser le projet et pour avancer proprement.

### Phase 1 - Stabiliser l'existant

Objectif :

- fiabiliser ce depot avant de le rapprocher du projet de reference.

A faire :

1. corriger la documentation ;
2. traiter le cas `dashboard_ai` manquant ;
3. clarifier les variables d'environnement ;
4. verifier les commandes de lancement.

### Phase 2 - Introduire le schema analytique

Objectif :

- ajouter la structure de donnees attendue par le projet de reference.

A faire :

1. ajouter dans `database/init.sql` les tables `dim_countries`, `dim_years`, `dim_operators`, `facts_night_trains`, `facts_country_stats` ;
2. ajouter la vue `dashboard_metrics` ;
3. choisir si ces tables vivent dans le meme schema PostgreSQL ou dans un schema dedie.

### Phase 3 - Refactorer l'ETL

Objectif :

- produire les donnees necessaires au nouveau schema analytique.

A faire :

1. enrichir `etl/sources.json` avec les vraies sources de reference ;
2. distinguer extraction brute, transformation analytique et chargement analytique ;
3. produire des fichiers `data/warehouse/` ;
4. normaliser pays / annees / operateurs ;
5. creer les jeux de donnees pour `facts_country_stats` et `facts_night_trains`.

### Phase 4 - Refactorer l'API

Objectif :

- rendre l'API compatible avec le dashboard du projet de reference.

A faire :

1. decouper `api/routes.py` en plusieurs routeurs ;
2. ajouter les schemas Pydantic correspondants ;
3. exposer les KPI, les stats, les analyses et les metadata ;
4. garder un endpoint health simple.

### Phase 5 - Rebrancher le dashboard sur l'API

Objectif :

- aligner l'interface avec le projet de reference.

A faire :

1. remplacer les requetes SQL directes par des appels HTTP vers l'API ;
2. ajouter des filtres globaux ;
3. reorganiser les pages du dashboard ;
4. brancher les rapports qualite et sources via l'API.

### Phase 6 - Verification et tests

Objectif :

- eviter les regressions.

A faire :

1. ajouter des tests API ;
2. valider les endpoints critiques ;
3. verifier la coherence entre ETL, base, API et dashboard.

---

## Correspondance entre les deux projets

Cette table permet de savoir "ou aller chercher" une idee dans le projet de reference.

| Besoin | Projet de reference | Projet cible actuel | Action recommandee |
|---|---|---|---|
| SQL analytique | `sql/01_init.sql` | `database/init.sql` | enrichir `database/init.sql` avec les tables analytiques |
| Modeles SQLAlchemy | `platform/server/app/models.py` | `database/models.py` | ajouter les modeles analytiques ou creer des modeles API dedies |
| API principale | `platform/server/app/main.py` | `api/main.py` | conserver FastAPI, mais modulariser |
| Routeurs API | `platform/server/app/routers/*.py` | `api/routes.py` | scinder `routes.py` en plusieurs fichiers |
| Schemas Pydantic | `platform/server/app/schemas/*.py` | `api/schemas.py` | separer les schemas par domaine |
| Dashboard | `platform/front/app.py` | `dashboard/app.py` | migrer vers un dashboard base sur l'API |
| ETL extraction | `etl/extract/*.py` | `etl/extract.py` | conserver le fetch generique si utile, mais ajouter les vraies sources |
| ETL transformation | `etl/transform/*.py` | `etl/transform.py` | ajouter une couche analytique et des sorties warehouse |
| ETL chargement | `etl/load/*.py` | `etl/load.py` | distinguer chargement traceabilite et chargement analytique |
| Tests | `platform/server/test/test_api.py` | absent | creer un dossier de tests |

---

## Ce qu'on va probablement faire ensuite

Si on suit la strategie recommandee, la suite logique sera :

1. corriger `docker-compose.yml` et stabiliser l'existant ;
2. enrichir `database/init.sql` pour ajouter le schema analytique ;
3. preparer les nouvelles sorties ETL ;
4. refactorer l'API en modules.

C'est l'ordre le plus propre pour avancer sans repartir de zero.

---

## Commandes utiles

### Lancer la base

```bash
docker compose up -d db
```

### Executer l'ETL

```bash
docker compose run --rm etl
```

### Lancer l'API et le dashboard

```bash
docker compose up -d api dashboard
```

### Voir les logs

```bash
docker compose logs -f
```

---

## Statut documentaire

Ce README sert maintenant de reference principale pour comprendre :

- l'etat actuel du projet cible ;
- les differences avec `MSPR_1_B3-main` ;
- ce qu'il manque ;
- dans quel ordre faire les modifications.

La prochaine etape recommandee est de commencer les modifications techniques en suivant la `Phase 1`, puis la `Phase 2`.
