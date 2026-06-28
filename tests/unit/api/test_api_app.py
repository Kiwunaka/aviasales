from __future__ import annotations

from fastapi.testclient import TestClient

from flight_hunter.api.app import create_app


def test_health_endpoint_reports_ready_without_external_credentials() -> None:
    client = TestClient(create_app())

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "app": "Flight Hunter",
        "status": "ok",
        "external_credentials_required": False,
    }


def test_providers_endpoint_exposes_disabled_reasons_without_secrets() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/providers")

    assert response.status_code == 200
    providers = {item["provider_id"]: item for item in response.json()["providers"]}
    assert providers["fake"]["enabled"] is True
    assert providers["aviasales_search"]["merge_scope"] == "provider_isolated"
    assert "credentials_missing" in providers["aviasales_search"]["blocked_reasons"]
    assert "token" not in str(response.json()).lower()


def test_search_endpoint_returns_demo_cached_result_and_provider_denials() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/searches",
        json={
            "origin": "WAW",
            "destination": "BCN",
            "departure_date": "2026-10-12",
            "return_date": "2026-10-19",
            "passengers": 2,
            "currency": "PLN",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["offers"][0]["provider_id"] == "fake"
    assert body["offers"][0]["freshness"] == "cached"
    assert body["offers"][0]["requires_live_confirmation"] is True
    assert body["offers"][0]["total_price"]["minor_units"] == 159800
    assert body["offers"][0]["ranking_reasons"] == [
        "cached_price",
        "requires_live_confirmation",
        "baggage_unknown",
    ]
    assert "aviasales_search" in body["denied_providers"]


def test_search_endpoint_accepts_explicit_passenger_mix() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/searches",
        json={
            "origin": "WAW",
            "destination": "BCN",
            "departure_date": "2026-10-12",
            "return_date": "2026-10-19",
            "passengers": 3,
            "adults": 2,
            "children": 1,
            "infants": 0,
            "trip_type": "round_trip",
            "currency": "PLN",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["offers"][0]["passengers"] == 3
    assert body["offers"][0]["total_price"]["minor_units"] == 239700


def test_search_endpoint_rejects_passenger_mix_total_mismatch() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/searches",
        json={
            "origin": "WAW",
            "destination": "BCN",
            "departure_date": "2026-10-12",
            "return_date": "2026-10-19",
            "passengers": 3,
            "adults": 1,
            "children": 0,
            "infants": 0,
            "trip_type": "round_trip",
            "currency": "PLN",
        },
    )

    assert response.status_code == 422


def test_providers_endpoint_can_show_aviasales_data_enabled_without_leaking_token(
    monkeypatch,
) -> None:
    monkeypatch.setenv("AVIASALES_DATA_ENABLED", "true")
    monkeypatch.setenv("TRAVELPAYOUTS_API_TOKEN", "secret-value")
    client = TestClient(create_app())

    response = client.get("/api/v1/providers")

    assert response.status_code == 200
    providers = {item["provider_id"]: item for item in response.json()["providers"]}
    assert providers["aviasales_data"]["enabled"] is True
    assert providers["aviasales_data"]["credentials_present"] is True
    assert "secret-value" not in str(response.json())
