from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import analysis, countries, dashboard, metadata, operators, statistics, trains
from routes import router as legacy_router

app = FastAPI(
    title="ObRail Europe API",
    description="API analytique pour les donnees ferroviaires europeennes.",
    version="2.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(countries.router)
app.include_router(trains.router)
app.include_router(dashboard.router)
app.include_router(statistics.router)
app.include_router(analysis.router)
app.include_router(operators.router)
app.include_router(metadata.router)
app.include_router(legacy_router)


@app.get("/")
def read_root():
    return {"status": "ok", "message": "API ObRail prete."}


@app.get("/health")
def health_check():
    return {"status": "ok"}
