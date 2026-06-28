from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from flight_hunter.api.app import create_app
from flight_hunter.persistence.models import mapper_registry

HOUSEHOLD_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
HOUSEHOLD_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
USER_A = "aaaaaaaa-0000-0000-0000-000000000001"
USER_B = "bbbbbbbb-0000-0000-0000-000000000001"


@pytest.mark.anyio
async def test_create_watch_requires_household_context() -> None:
    client = TestClient(create_app(watch_session_factory=await _session_factory()))

    response = client.post(
        "/api/v1/watches",
        json=_watch_payload(),
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "auth_context_missing",
        "message": "household context is required",
    }


@pytest.mark.anyio
async def test_create_watch_and_list_only_same_household() -> None:
    client = TestClient(create_app(watch_session_factory=await _session_factory()))

    created_a = client.post(
        "/api/v1/watches",
        headers=_headers(HOUSEHOLD_A, USER_A),
        json=_watch_payload(origin="waw", destination="bcn"),
    )
    created_b = client.post(
        "/api/v1/watches",
        headers=_headers(HOUSEHOLD_B, USER_B),
        json=_watch_payload(origin="WAW", destination="NRT"),
    )
    list_a = client.get("/api/v1/watches", headers=_headers(HOUSEHOLD_A, USER_A))

    assert created_a.status_code == 201
    assert created_b.status_code == 201
    assert UUID(created_a.json()["id"])
    assert created_a.json()["origin"] == "WAW"
    assert created_a.json()["destination"] == "BCN"
    assert created_a.json()["enabled"] is True
    assert [item["destination"] for item in list_a.json()["watches"]] == ["BCN"]


def _headers(household_id: str, user_id: str) -> dict[str, str]:
    return {
        "X-Flight-Hunter-Household-Id": household_id,
        "X-Flight-Hunter-User-Id": user_id,
    }


def _watch_payload(
    *,
    origin: str = "WAW",
    destination: str = "BCN",
) -> dict[str, object]:
    return {
        "origin": origin,
        "destination": destination,
        "departure_date": "2026-10-12",
        "return_date": "2026-10-19",
    }


async def _session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(mapper_registry.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)
