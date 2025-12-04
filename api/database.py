import os
from sqlalchemy import create_engine
import logging

# Configuration du logging
logger = logging.getLogger("uvicorn")

# Récupération de l'URL depuis les variables d'environnement
DATABASE_URL = os.getenv('DATABASE_URL')

# Création du moteur de base de données
try:
    if not DATABASE_URL:
        logger.warning("⚠️ DATABASE_URL non définie, l'API risque de ne pas fonctionner.")
        engine = None
    else:
        engine = create_engine(DATABASE_URL)
        logger.info("✅ Connecteur BDD initialisé.")
except Exception as e:
    logger.error(f"❌ Erreur lors de la création du moteur SQL : {e}")
    engine = None