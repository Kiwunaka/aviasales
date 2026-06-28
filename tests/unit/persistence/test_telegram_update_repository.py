from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from flight_hunter.persistence.models import mapper_registry
from flight_hunter.persistence.repositories import TelegramUpdateRepository

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)


@pytest.mark.anyio
async def test_telegram_update_repository_records_update_id_once_across_sessions() -> None:
    session_factory = await _session_factory()

    async with session_factory() as session:
        repository = TelegramUpdateRepository(session)
        first = await repository.record_update(update_id=1001, received_at=NOW)
        await session.commit()

    async with session_factory() as session:
        repository = TelegramUpdateRepository(session)
        second = await repository.record_update(update_id=1001, received_at=NOW)
        await session.commit()

    assert first is True
    assert second is False


async def _session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(mapper_registry.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)
