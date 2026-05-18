def test_metrics_endpoint_exposes_business_and_health_metrics(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    payload = response.text
    assert "obrail_api_healthy" in payload
    assert "obrail_database_connected" in payload
    assert "obrail_quality_report_available" in payload
    assert "obrail_model_metrics_available" in payload
