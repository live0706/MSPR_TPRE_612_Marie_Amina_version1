import pytest


@pytest.mark.integration
def test_stats_volumes_endpoint(client, seeded_db):
    response = client.get(
        "/stats/volumes",
        params={"country_code": seeded_db["country_code"], "year": 2026, "limit": 20},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload
    matching_rows = [item for item in payload if item["country_code"] == seeded_db["country_code"]]
    assert matching_rows
    assert matching_rows[0]["year"] == 2026
    assert matching_rows[0]["total_trajets"] >= 1


def test_monitoring_summary_endpoint_shape(client, monkeypatch):
    monkeypatch.setattr("routers.monitoring.ping_database", lambda: True)
    monkeypatch.setattr(
        "routers.monitoring.fetch_one",
        lambda *args, **kwargs: {
            "total_trips": 10,
            "total_countries": 4,
            "total_operators": 2,
            "latest_ingestion_at": None,
        },
    )
    monkeypatch.setattr("routers.monitoring.ensure_db", lambda: None)

    response = client.get("/api/monitoring/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["database_connected"] is True
    assert payload["total_trips"] == 10
