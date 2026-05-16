import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from database import DatabaseUnavailableError, QueryExecutionError

logger = logging.getLogger("obrail.errors")


def _error_payload(code: str, message: str, details=None):
    payload = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return payload


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("Erreur de validation sur %s: %s", request.url.path, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_payload("validation_error", "Parametres invalides.", exc.errors()),
        )

    @app.exception_handler(DatabaseUnavailableError)
    async def database_unavailable_handler(request: Request, exc: DatabaseUnavailableError):
        logger.error("Base indisponible sur %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_error_payload("database_unavailable", str(exc)),
        )

    @app.exception_handler(QueryExecutionError)
    async def query_execution_handler(request: Request, exc: QueryExecutionError):
        logger.error("Erreur SQL sur %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload("query_execution_error", str(exc)),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning("Erreur HTTP %s sur %s: %s", exc.status_code, request.url.path, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload("http_error", str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Erreur non geree sur %s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload("internal_server_error", "Une erreur interne est survenue."),
        )
