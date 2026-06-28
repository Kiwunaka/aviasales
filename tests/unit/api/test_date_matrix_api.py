from __future__ import annotations

from fastapi.testclient import TestClient

from flight_hunter.api.app import create_app


def test_date_matrix_endpoint_returns_unpriced_planning_cells() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/searches/date-matrix",
        json={
            "departure_date": "2026-10-12",
            "return_date": "2026-10-19",
            "flexibility_days": 3,
            "min_stay_days": 6,
            "max_stay_days": 8,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_calls_required"] == 0
    assert body["priced"] is False
    assert body["cells"]
    assert all(6 <= cell["stay_days"] <= 8 for cell in body["cells"])
