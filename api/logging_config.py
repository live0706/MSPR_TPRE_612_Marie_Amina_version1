import logging
from logging.config import dictConfig

from config import LOG_LEVEL


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": LOG_LEVEL,
                }
            },
            "root": {"handlers": ["default"], "level": LOG_LEVEL},
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": LOG_LEVEL, "propagate": False},
                "uvicorn.error": {"handlers": ["default"], "level": LOG_LEVEL, "propagate": False},
                "uvicorn.access": {"handlers": ["default"], "level": LOG_LEVEL, "propagate": False},
                "obrail": {"handlers": ["default"], "level": LOG_LEVEL, "propagate": False},
            },
        }
    )
    logging.getLogger("obrail").info("Configuration du logging API chargee")
