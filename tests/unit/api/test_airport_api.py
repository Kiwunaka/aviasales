from __future__ import annotations

from fastapi.testclient import TestClient

from flight_hunter.api.app import create_app


def test_airport_autocomplete_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/airports/autocomplete", params={"q": "wars"})

    assert response.status_code == 200
    body = response.json()
    assert body["airports"][0]["iata_code"] == "WAW"
    assert body["airports"][0]["label"] == "WAW - Warsaw Chopin Airport, Warsaw"


def test_airport_nearby_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/airports/nearby", params={"iata_code": "WAW", "radius_km": 150})

    assert response.status_code == 200
    body = response.json()
    assert [item["iata_code"] for item in body["airports"]] == ["WMI", "LCJ"]
    assert body["airports"][0]["distance_km"] == 38
    assert "not implied" in body["airports"][0]["transfer_note"]
