import uuid

from fastapi import APIRouter, HTTPException, status

from prediction_service import PredictionModelUnavailable, predict_co2
from schemas.prediction import PredictionRequest, PredictionResponse

router = APIRouter(tags=["Prediction"])


@router.post("/predict", response_model=PredictionResponse, summary="Predire les emissions CO2 d'un trajet")
def predict(payload: PredictionRequest):
    try:
        prediction = predict_co2(payload)
    except PredictionModelUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return {
        "predicted_co2_emissions": prediction,
        "unit": "kgCO2e",
        "model_name": "co2_emissions_model",
        "model_version": "tpre622-v1",
        "request_id": str(uuid.uuid4()),
    }
