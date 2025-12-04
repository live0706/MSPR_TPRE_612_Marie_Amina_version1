from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router as api_router

# --- CONFIGURATION DE L'APPLICATION ---
app = FastAPI(
    title="ObRail Europe API",
    description="API REST modulaire pour les données ferroviaires.",
    version="1.1.0"
)

# Configuration CORS (Pour autoriser le Dashboard à parler à l'API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod, remplacez "*" par l'URL du frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- INCLUSION DES ROUTES ---
app.include_router(api_router)

# --- ROUTE DE SANTÉ (Health Check) ---
@app.get("/")
def health_check():
    """Vérifie que le serveur est en ligne."""
    return {"status": "ok", "message": "API ObRail prête."}