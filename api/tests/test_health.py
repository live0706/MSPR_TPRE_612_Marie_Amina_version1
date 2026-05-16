def test_health_endpoint_returns_status(client, monkeypatch):
    monkeypatch.setattr("routers.health.ping_database", lambda: True)
    monkeypatch.setattr("routers.health.QUALITY_REPORT_PATH", type("PathStub", (), {"exists": lambda self: True})())
    monkeypatch.setattr("routers.health.MODEL_METRICS_PATH", type("PathStub", (), {"exists": lambda self: True})())

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"]["status"] == "ok"
    assert "timestamp" in payload


def test_trajets_validation_error_payload(client):
    response = client.get("/trajets", params={"limit": 0})

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
