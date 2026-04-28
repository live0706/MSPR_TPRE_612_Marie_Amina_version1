🚄 ObRail Europe : Plateforme Analytique Big Data Ferroviaire
📖 Présentation du projet
ObRail Europe est une solution de Business Intelligence (BI) "End-to-End" conçue pour auditer, analyser et visualiser l'offre ferroviaire longue distance en Europe sur la période 2010-2026.

La plateforme automatise la découverte de sources de données (Crawl d'API), leur ingestion massive (Multi-threading), et leur transformation analytique pour fournir des métriques précises sur les émissions de CO2 et la connectivité transfrontalière.

🏗 Architecture de la Solution
L'écosystème ObRail est divisé en quatre services conteneurisés :

Ingestion & ETL (Python) : Découverte dynamique de flux GTFS via l'API Transitland et traitement parallèle.

Stockage (PostgreSQL 15) : Modèle hybride associant une couche transactionnelle (Audit) et une couche analytique (Schéma en étoile).

Restitution (FastAPI) : API REST modulaire servant les indicateurs de performance (KPI).

Visualisation (Streamlit) : Dashboards décisionnels et monitoring de la qualité des données (IA Quality).

📂 Organisation du Dépôt
Plaintext
.
├── api/                       # Service API REST (FastAPI)
│   ├── routers/               # Endpoints : analysis, statistics, trains, etc.
│   ├── schemas/               # Validation des contrats de données Pydantic
│   ├── database.py            # Connexion à la base via SQLAlchemy
│   └── main.py                # Point d'entrée de l'API
├── dashboard/                 # Interface de visualisation
│   ├── app.py                 # Dashboard analytique principal
│   └── app_ai.py              # Monitoring de la qualité & Métriques modèles
├── data/                      # Data Lake local
│   ├── raw/                   # Données brutes téléchargées (ZIP, CSV)
│   └── processed/             # Données nettoyées et prêtes pour le chargement
├── database/                  # Couche de persistance SQL
│   ├── init.sql               # Schéma relationnel de base
│   └── analytics.sql   # Couche analytique (Dimensions & Faits)
└── etl/                       # Pipeline Data Engineering (Le coeur du projet)
    ├── discover.py            # Crawling automatique des API européennes
    ├── extract.py             # Fetcher multi-threadé haute performance
    ├── gtfs.py                # Parser GTFS (Gestion temporelle 2010-2026)
    ├── transform.py           # Calcul Haversine & CO2 (Filtre > 400km)
    ├── load.py                # Ingestion SQL optimisée
    └── main_etl.py            # Chef d'orchestre du pipeline
⚡ Fonctionnalités Avancées
1. Ingestion Massive & Parallélisation
Contrairement aux systèmes séquentiels, ObRail utilise un MassiveFetcher basé sur ThreadPoolExecutor. Cela permet de télécharger et de traiter simultanément plusieurs flux nationaux (SNCF, DB, ÖBB, Renfe), réduisant le temps d'ingestion de 80%.

2. "Temporal Awareness" (2010-2026)
Le module gtfs.py analyse les métadonnées de chaque flux (feed_info.txt) pour ancrer les données temporelles. Cette approche permet de traiter sans distinction des archives de 2010 et des prévisions de 2026 au sein d'un même référentiel.

3. Schéma Analytique (Warehouse)
Le projet implémente un modèle en étoile pour optimiser les performances de lecture :

Faits : facts_night_trains (Indicateurs par trajet), facts_country_stats (Agrégats nationaux).

Dimensions : dim_countries, dim_operators, dim_years.

🚀 Guide de démarrage
Lancement avec Docker Compose
Pour démarrer l'ensemble de l'infrastructure (Base de données, API, Dashboard) :

Bash
docker compose up -d --build api dashboard
Exécution du Pipeline ETL
Pour déclencher la découverte et l'ingestion automatique des données européennes :

Bash
docker compose run --rm etl
Consultation des résultats
Dashboard : http://localhost:8501


🛠 Stack Technique
Langage : Python 3.11

Data : Pandas, SQLAlchemy, PyArrow

API : FastAPI, Pydantic

Frontend : Streamlit

Infrastructure : Docker, PostgreSQL

📊 Indicateurs Clés (KPI)
Connectivité : Analyse des trajets ferroviaires supérieurs à 400 km.

Impact Éco : Calcul des émissions de CO2 basé sur les facteurs d'émission réels des réseaux nationaux.

Qualité : Monitoring de la complétude et de la validité des flux via le rapport de qualité automatisé.
