from __future__ import annotations

from fastapi.testclient import TestClient

from flight_hunter.api.app import create_app


def test_admin_provider_health_returns_provider_status_without_secrets(monkeypatch) -> None:
    monkeypatch.setenv("TRAVELPAYOUTS_API_TOKEN", "secret-value")
    monkeypatch.setenv("AVIASALES_DATA_ENABLED", "true")
    client = TestClient(create_app())

    response = client.get("/api/v1/admin/providers/health")

    assert response.status_code == 200
    body = response.json()
    assert body["checked_at"]
    providers = {provider["provider_id"]: provider for provider in body["providers"]}
    assert providers["aviasales_data"]["credentials_present"] is True
    assert providers["aviasales_data"]["secret_present"] is True
    assert "secret-value" not in str(body)
    assert "TRAVELPAYOUTS_API_TOKEN" not in str(body)
