# 🚄 ObRail Europe : Plateforme Analytique Big Data Ferroviaire

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Docker](https://img.shields.io/badge/docker-enabled-blue.svg)
![FastAPI](https://img.shields.io/badge/API-FastAPI-green.svg)
![PostgreSQL](https://img.shields.io/badge/DB-PostgreSQL%2015-blue.svg)

## 📖 Présentation du projet
**ObRail Europe** est une solution de Business Intelligence (BI) "End-to-End" conçue pour auditer, analyser et visualiser l'offre ferroviaire longue distance en Europe sur la période **2010-2026**.

La plateforme automatise la découverte de sources de données (Crawl d'API), leur ingestion massive (Multi-threading), et leur transformation analytique pour fournir des métriques précises sur les émissions de CO2 et la connectivité transfrontalière.

---

## 🏗 Architecture de la Solution
L'écosystème ObRail est divisé en quatre services conteneurisés :

*   **Ingestion & ETL (Python)** : Découverte dynamique de flux GTFS via l'API Transitland et traitement parallèle.
*   **Stockage (PostgreSQL 15)** : Modèle hybride associant une couche transactionnelle (Audit) et une couche analytique (Schéma en étoile).
*   **Restitution (FastAPI)** : API REST modulaire servant les indicateurs de performance (KPI).
*   **Visualisation (Streamlit)** : Dashboards décisionnels et monitoring de la qualité des données (IA Quality).

---

## 📂 Organisation du Dépôt
```plaintext
.
├── api/                # Service API REST (FastAPI)
│   ├── routers/        # Endpoints : analysis, statistics, trains, etc.
│   ├── schemas/        # Validation des contrats de données Pydantic
│   ├── database.py     # Connexion à la base via SQLAlchemy
│   └── main.py         # Point d'entrée de l'API
├── dashboard/          # Interface de visualisation
│   ├── app.py          # Dashboard analytique principal
├── data/               # Data Lake local
│   ├── raw/            # Données brutes téléchargées (ZIP, CSV)
│   └── processed/      # Données nettoyées et prêtes pour le chargement
├── database/           # Couche de persistance SQL
│   ├── init.sql        # Schéma relationnel de base
│   └── analytics.sql   # Couche analytique (Dimensions & Faits)
└── etl/                # Pipeline Data Engineering (Le cœur du projet)
    ├── discover.py     # Crawling automatique des API européennes
    ├── extract.py      # Fetcher multi-threadé haute performance
    ├── transform.py    # Calcul Haversine & CO2 (Filtre > 100km)
    ├── load.py         # Ingestion SQL optimisée
    └── main_etl.py     # Chef d'orchestre du pipeline
```

🚀 Guide de démarrage
1. Lancement avec Docker Compose
Pour démarrer l'ensemble de l'infrastructure (Base de données, API, Dashboard) :

Bash
docker compose up -d --build

2. Exécution du Pipeline ETL
Pour déclencher la découverte, le filtrage et l'ingestion automatique (cible > 10 000 trajets) :

Bash
docker compose run --rm etl

3. Consultation des résultats
Dashboard : http://localhost:8501


🛠 Stack Technique
Langage : Python 3.11

Data : Pandas, SQLAlchemy, PyArrow, NumPy

API : FastAPI, Pydantic, Uvicorn

Frontend : Streamlit

Infrastructure : Docker, PostgreSQL 15

📊 Indicateurs Clés (KPI)
Connectivité : Analyse des trajets ferroviaires supérieurs à 100 km (Longue Distance).

Impact Éco : Calcul des émissions de CO2 basé sur les facteurs d'émission réels des réseaux nationaux.

Qualité (IA) : Monitoring de la complétude et de la validité des flux via des rapports de qualité automatisés.
