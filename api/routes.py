from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from typing import List, Optional

# Imports internes
from database import engine
from schemas import TrainSchema

# Création du routeur
router = APIRouter()

@router.get("/trains", response_model=List[TrainSchema])
def get_trains(
    limit: int = 20, 
    offset: int = 0, 
    service_type: Optional[str] = Query(None, enum=["Jour", "Nuit"])
):
    """
    Récupère la liste des trains avec filtrage et pagination.
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Base de données non connectée.")

    try:
        query = "SELECT * FROM trips"
        params = {}
        
        # Filtre dynamique
        if service_type:
            query += " WHERE service_type = :service_type"
            params['service_type'] = service_type
            
        # Pagination
        query += " LIMIT :limit OFFSET :offset"
        params['limit'] = limit
        params['offset'] = offset

        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            # Conversion en dictionnaires pour Pydantic
            rows = result.mappings().all()
            return rows
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur SQL: {str(e)}")

@router.get("/stats")
def get_stats():
    """
    Renvoie des statistiques globales (Compteurs Jour/Nuit).
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Base de données non connectée.")
        
    try:
        with engine.connect() as conn:
            # Requêtes d'agrégation
            total = conn.execute(text("SELECT COUNT(*) FROM trips")).scalar()
            night = conn.execute(text("SELECT COUNT(*) FROM trips WHERE service_type='Nuit'")).scalar()
            day = conn.execute(text("SELECT COUNT(*) FROM trips WHERE service_type='Jour'")).scalar()
            
        return {
            "total_trains": total,
            "breakdown": {
                "night_trains": night,
                "day_trains": day,
                "night_share_percentage": round((night / total * 100), 2) if total > 0 else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))