# Decisions

## Decouverte des datasets
On utilise la decouverte OpenDataSoft pour garder des sources a jour et heterogenes. Une source Wikipedia fixe sert de base stable.

## Stockage
PostgreSQL stocke le dataset normalise. Des index ciblent les filtres courants de l'API.

## API
FastAPI fournit une interface REST minimale pour la liste et les stats de base.

## Dashboard
Streamlit est utilise pour iterer vite et afficher des KPI clairement.

## Metriques de modele
Une regression lineaire simple (CO2 vs distance) sert de signal predictif et de metrique de suivi.
