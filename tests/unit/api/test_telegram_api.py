from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from flight_hunter.api.app import create_app
from flight_hunter.persistence.models import mapper_registry


def test_telegram_webhook_is_disabled_by_default() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/telegram/webhook",
        json={"update_id": 1001, "message": {"text": "/start"}},
    )

    assert response.status_code == 503
    assert response.json() == {"code": "telegram_disabled", "status": "rejected"}


def test_telegram_webhook_requires_secret_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "secret")
    client = TestClient(create_app(watch_session_factory=asyncio.run(_session_factory())))

    response = client.post(
        "/api/v1/telegram/webhook",
        json={"update_id": 1001, "message": {"text": "/start"}},
    )

    assert response.status_code == 403
    assert response.json() == {"code": "secret_mismatch", "status": "rejected"}


def test_telegram_webhook_accepts_and_deduplicates_update(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "secret")
    client = TestClient(create_app(watch_session_factory=asyncio.run(_session_factory())))
    headers = {"X-Telegram-Bot-Api-Secret-Token": "secret"}
    payload = {"update_id": 1001, "message": {"text": "/start"}}

    first = client.post("/api/v1/telegram/webhook", json=payload, headers=headers)
    second = client.post("/api/v1/telegram/webhook", json=payload, headers=headers)

    assert first.status_code == 202
    assert first.json() == {"code": "accepted", "status": "accepted"}
    assert second.status_code == 200
    assert second.json() == {"code": "duplicate", "status": "ignored"}


def test_telegram_webhook_deduplicates_update_across_app_instances(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "secret")
    session_factory = asyncio.run(_session_factory())
    headers = {"X-Telegram-Bot-Api-Secret-Token": "secret"}
    payload = {"update_id": 2002, "message": {"text": "/start"}}

    first_client = TestClient(create_app(watch_session_factory=session_factory))
    first = first_client.post("/api/v1/telegram/webhook", json=payload, headers=headers)

    second_client = TestClient(create_app(watch_session_factory=session_factory))
    second = second_client.post("/api/v1/telegram/webhook", json=payload, headers=headers)

    assert first.status_code == 202
    assert first.json() == {"code": "accepted", "status": "accepted"}
    assert second.status_code == 200
    assert second.json() == {"code": "duplicate", "status": "ignored"}


async def _session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(mapper_registry.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)
