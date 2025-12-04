OBRAIL-PROJECT/
│
├── 📄 docker-compose.yml       # Orchestrateur : Déploiement des 4 services (DB, ETL, API, Dash)
├── 📄 .env                     # Sécurité : Variables d'environnement (Mots de passe, Clés)
├── 📄 .gitignore               # Git : Exclusion des fichiers sensibles et temporaires
├── 📄 README.md                # Documentation : Guide d'installation et de lancement
│
├── 📂 data/                    # STOCKAGE & TRAÇABILITÉ
│   ├── raw/                    # Données brutes collectées (JSON, CSV, HTML) - Copie immuable
│   └── processed/              # Données nettoyées prêtes pour l'import - Format unifié
│
├── 📂 database/                # SERVICE PERSISTANCE (PostgreSQL)
│   └── init.sql                # Script DDL : Création du schéma (Tables Gares, Trajets...)
│
├── 📂 etl/                     # SERVICE TRAITEMENT (Python Script)
│   ├── Dockerfile              # Image Docker pour l'ETL
│   ├── requirements.txt        # Dépendances : pandas, requests, beautifulsoup4, sqlalchemy
│   ├── extract.py              # Scripts de collecte (API & Scraping)
│   ├── transform.py            # Logique métier : Nettoyage & Calcul CO2
│   ├── load.py                 # Script de chargement en base
│   └── main_etl.py             # Point d'entrée de l'automatisation
│
├── 📂 api/                     # SERVICE BACKEND (FastAPI)
│   ├── Dockerfile              # Image Docker pour l'API
│   ├── requirements.txt        # Dépendances : fastapi, uvicorn, pydantic, sqlalchemy
│   ├── main.py                 # Application principale et config Swagger UI
│   ├── database.py             # Gestion de la connexion BDD (Session)
│   ├── routes.py               # Définition des Endpoints REST (GET /trains...)
│   └── schemas.py              # Modèles de validation des données (Pydantic)
│
├── 📂 dashboard/               # SERVICE FRONTEND (Streamlit)
│   ├── Dockerfile              # Image Docker pour le Dashboard
│   ├── requirements.txt        # Dépendances : streamlit, pandas, plotly, psycopg2
│   └── app.py                  # Code de l'interface de contrôle qualité
│
├── 📂 tests/                   # ASSURANCE QUALITÉ (QA)
│   ├── test_etl.py             # Tests unitaires du nettoyage des données
│   └── test_api.py             # Tests d'intégration des endpoints API
│
└── 📂 docs/                    # DOCUMENTATION TECHNIQUE
    ├── architecture_diagram.png # Schéma de l'architecture Docker
    ├── mcd_diagram.png          # Modèle Conceptuel de Données
    └── user_guide.md            # Manuel d'utilisation pour les partenaires