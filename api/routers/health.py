from fastapi import APIRouter

from health_state import build_health_payload
from schemas.health import HealthResponse

router = APIRouter(tags=["Sante"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Verifier l'etat de sante de l'API",
    description="Controle la disponibilite de l'API, de la base PostgreSQL et des fichiers de qualite/modeles.",
)
def health_check():
    return build_health_payload()
