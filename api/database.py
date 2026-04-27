import logging
import os

from sqlalchemy import create_engine, text

logger = logging.getLogger("uvicorn")

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    if not DATABASE_URL:
        logger.warning("DATABASE_URL non definie, l'API risque de ne pas fonctionner.")
        engine = None
    else:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10},
        )
        logger.info("Connecteur BDD initialise avec succes.")
except Exception as exc:
    logger.error(f"Erreur lors de la creation du moteur SQL : {exc}")
    engine = None


def fetch_all(query, params=None):
    if engine is None:
        return []
    with engine.connect() as connection:
        result = connection.execute(text(query), params or {})
        return result.mappings().all()


def fetch_one(query, params=None):
    if engine is None:
        return None
    with engine.connect() as connection:
        result = connection.execute(text(query), params or {})
        return result.mappings().first()
