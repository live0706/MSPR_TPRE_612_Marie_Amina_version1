import logging
import os
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("obrail.database")

engine: Engine | None = None


class DatabaseUnavailableError(RuntimeError):
    pass


class QueryExecutionError(RuntimeError):
    pass


def _build_engine(database_url: str) -> Engine:
    engine_kwargs: dict[str, Any] = {"pool_pre_ping": True, "future": True}
    if database_url.startswith("postgresql"):
        engine_kwargs["connect_args"] = {"connect_timeout": 10}
    return create_engine(database_url, **engine_kwargs)


def init_engine(database_url: str | None = None) -> Engine | None:
    global engine

    resolved_database_url = database_url or os.getenv("DATABASE_URL")
    if not resolved_database_url:
        logger.warning("DATABASE_URL non definie, l'API fonctionnera en mode degrade.")
        engine = None
        return None

    try:
        engine = _build_engine(resolved_database_url)
        logger.info("Moteur SQL initialise avec succes.")
        return engine
    except Exception as exc:
        logger.error("Erreur lors de la creation du moteur SQL: %s", exc)
        engine = None
        return None


def get_engine() -> Engine:
    global engine
    if engine is None:
        init_engine()
    if engine is None:
        raise DatabaseUnavailableError("Base de donnees non configuree ou non joignable.")
    return engine


def dispose_engine() -> None:
    global engine
    if engine is not None:
        engine.dispose()
        logger.info("Moteur SQL ferme proprement.")
    engine = None


def ping_database() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("Ping BDD en echec: %s", exc)
        return False


def fetch_all(query: str, params: dict[str, Any] | None = None):
    try:
        with get_engine().connect() as connection:
            result = connection.execute(text(query), params or {})
            return result.mappings().all()
    except DatabaseUnavailableError:
        raise
    except SQLAlchemyError as exc:
        raise QueryExecutionError(f"Impossible d'executer la requete: {exc}") from exc


def fetch_one(query: str, params: dict[str, Any] | None = None):
    try:
        with get_engine().connect() as connection:
            result = connection.execute(text(query), params or {})
            return result.mappings().first()
    except DatabaseUnavailableError:
        raise
    except SQLAlchemyError as exc:
        raise QueryExecutionError(f"Impossible d'executer la requete: {exc}") from exc


def execute_sql(query: str, params: dict[str, Any] | None = None) -> None:
    try:
        with get_engine().begin() as connection:
            connection.execute(text(query), params or {})
    except DatabaseUnavailableError:
        raise
    except SQLAlchemyError as exc:
        raise QueryExecutionError(f"Impossible d'executer la requete d'ecriture: {exc}") from exc
