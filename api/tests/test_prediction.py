from prediction_service import PredictionModelUnavailable


def _valid_payload():
    return {
        "distance_km": 604.0,
        "operator_name": "SNCF",
        "service_type": "Nuit",
        "train_type": "Rail",
        "country": "FR",
        "departure_time": "2026-12-01T19:30:00",
        "arrival_time": "2026-12-02T07:10:00",
        "origin_lat": 48.8566,
        "origin_lon": 2.3522,
        "destination_lat": 45.764,
        "destination_lon": 4.8357,
    }


def test_predict_returns_co2_estimate(client, monkeypatch):
    monkeypatch.setattr("routers.prediction.predict_co2", lambda payload: 1.208)

    response = client.post("/predict", json=_valid_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["predicted_co2_emissions"] == 1.208
    assert payload["unit"] == "kgCO2e"
    assert payload["model_name"] == "co2_emissions_model"
    assert payload["model_version"] == "tpre622-v1"
    assert payload["request_id"]


def test_predict_rejects_missing_distance(client):
    payload = _valid_payload()
    payload.pop("distance_km")

    response = client.post("/predict", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_predict_rejects_non_positive_distance(client):
    payload = _valid_payload()
    payload["distance_km"] = 0

    response = client.post("/predict", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_predict_returns_503_when_model_is_missing(client, monkeypatch):
    def raise_unavailable(payload):
        raise PredictionModelUnavailable("Modele de prediction absent")

    monkeypatch.setattr("routers.prediction.predict_co2", raise_unavailable)

    response = client.post("/predict", json=_valid_payload())

    assert response.status_code == 503
    assert "Modele de prediction absent" in response.json()["error"]["message"]
