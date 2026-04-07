from pydantic import BaseModel
from typing import Optional

class TrainSchema(BaseModel):
    """
    Modèle de données pour un Train (sérialisation JSON).
    Utilisé pour valider les réponses de l'API.
    """
    trip_id: str
    operator_name: Optional[str] = None
    origin_city: Optional[str] = None
    destination_city: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    service_type: Optional[str] = None
    train_type: Optional[str] = None
    distance_km: Optional[float] = None
    co2_emissions: Optional[float] = 0.0

    class Config:
        # Permet à Pydantic de lire les objets SQLAlchemy (ORM)
        from_attributes = True
