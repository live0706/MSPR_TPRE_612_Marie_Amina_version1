def test_health_endpoint_returns_status(client, monkeypatch):
    monkeypatch.setattr(
        "routers.health.build_health_payload",
        lambda: {
            "status": "ok",
            "environment": "test",
            "version": "2.1.0",
            "timestamp": "2026-05-18T10:15:00Z",
            "database": {"status": "ok", "detail": "Connexion PostgreSQL operationnelle."},
            "quality_report": {"status": "ok", "detail": "Rapport de qualite disponible."},
            "model_metrics": {"status": "ok", "detail": "Metriques modele disponibles."},
        },
    )

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
