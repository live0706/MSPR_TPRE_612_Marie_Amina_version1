import pytest


@pytest.mark.integration
def test_get_trajets_with_filters(client, seeded_db):
    response = client.get(
        "/trajets",
        params={
            "country_code": seeded_db["country_code"],
            "operator_name": "PyTest",
            "search": "PyTest City",
            "limit": 10,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert any(item["trip_id"] == seeded_db["trip_id"] for item in payload)


@pytest.mark.integration
def test_get_trajet_detail(client, seeded_db):
    response = client.get(f"/trajets/{seeded_db['trip_id']}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["trip_id"] == seeded_db["trip_id"]
    assert payload["operator_name"] == seeded_db["operator_name"]
    assert payload["country_code"] == seeded_db["country_code"]


def test_get_trajet_invalid_identifier(client):
    response = client.get("/trajets/$$$")

    assert response.status_code == 422
