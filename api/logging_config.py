import logging
from logging.config import dictConfig

from config import APP_LOG_PATH, LOG_LEVEL


def configure_logging() -> None:
    APP_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

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
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "standard",
                    "filename": str(APP_LOG_PATH),
                    "maxBytes": 10485760,
                    "backupCount": 5,
                    "encoding": "utf-8",
                    "level": LOG_LEVEL,
                }
            },
            "root": {"handlers": ["default", "file"], "level": LOG_LEVEL},
            "loggers": {
                "uvicorn": {"handlers": ["default", "file"], "level": LOG_LEVEL, "propagate": False},
                "uvicorn.error": {"handlers": ["default", "file"], "level": LOG_LEVEL, "propagate": False},
                "uvicorn.access": {"handlers": ["default", "file"], "level": LOG_LEVEL, "propagate": False},
                "obrail": {"handlers": ["default", "file"], "level": LOG_LEVEL, "propagate": False},
            },
        }
    )
    logging.getLogger("obrail").info("Configuration du logging API chargee")
