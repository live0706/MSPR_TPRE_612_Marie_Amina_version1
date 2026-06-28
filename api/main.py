import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from config import APP_DESCRIPTION, APP_NAME, APP_VERSION, CORS_ORIGINS, ENABLE_PROMETHEUS
from database import dispose_engine, init_engine
from errors import register_exception_handlers
from logging_config import configure_logging
from metrics import register_business_metrics
from routers import analysis, countries, dashboard, metadata, operators, prediction, statistics, trains
from routers.health import router as health_router
from routers.journeys import router as journeys_router
from routers.monitoring import router as monitoring_router
from routes import router as legacy_router

try:
    from prometheus_fastapi_instrumentator import Instrumentator
except ModuleNotFoundError:  # pragma: no cover - fallback local si dependance absente
    Instrumentator = None

configure_logging()
logger = logging.getLogger("obrail.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Demarrage de l'API ObRail")
    init_engine()
    yield
    dispose_engine()
    logger.info("Arret de l'API ObRail")


app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Sante", "description": "Verification d'etat et disponibilite du service."},
        {"name": "Trajets", "description": "Consultation et detail des trajets ferroviaires."},
        {"name": "Monitoring", "description": "Resume d'observabilite et liens de supervision."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "request_id=%s method=%s path=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            duration_ms,
        )
    except Exception:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "request_id=%s method=%s path=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            duration_ms,
        )
        raise
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


register_exception_handlers(app)

app.include_router(health_router)
app.include_router(journeys_router)
app.include_router(monitoring_router)
app.include_router(countries.router)
app.include_router(trains.router)
app.include_router(dashboard.router)
app.include_router(statistics.router)
app.include_router(analysis.router)
app.include_router(operators.router)
app.include_router(metadata.router)
app.include_router(prediction.router)
app.include_router(legacy_router)

if ENABLE_PROMETHEUS and Instrumentator is not None:
    register_business_metrics()
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics"],
        env_var_name=None,
    ).instrument(app).expose(app, include_in_schema=False)
elif ENABLE_PROMETHEUS:
    logger.warning("Prometheus active par configuration mais dependance non installee.")


@app.get("/", tags=["Sante"], summary="Accueil API")
def read_root():
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
        "docs": "/api/docs",
        "health": "/health",
        "metrics": "/metrics" if ENABLE_PROMETHEUS else None,
    }
