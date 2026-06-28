from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from flight_hunter.persistence.models import mapper_registry
from flight_hunter.persistence.repositories import HouseholdWatchRepository, NewWatch

HOUSEHOLD_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
HOUSEHOLD_B = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
WATCH_A = UUID("11111111-1111-1111-1111-111111111111")
WATCH_B = UUID("22222222-2222-2222-2222-222222222222")
NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)


@pytest.mark.anyio
async def test_repository_lists_only_watches_for_requested_household() -> None:
    session_factory = await _session_factory()
    async with session_factory() as session:
        repository = HouseholdWatchRepository(session)
        await repository.add_watch(
            NewWatch(
                id=WATCH_A,
                household_id=HOUSEHOLD_A,
                owner_user_id=UUID("aaaaaaaa-0000-0000-0000-000000000001"),
                origin="WAW",
                destination="BCN",
                departure_date="2026-10-12",
                return_date="2026-10-19",
                created_at=NOW,
            )
        )
        await repository.add_watch(
            NewWatch(
                id=WATCH_B,
                household_id=HOUSEHOLD_B,
                owner_user_id=UUID("bbbbbbbb-0000-0000-0000-000000000001"),
                origin="WAW",
                destination="NRT",
                departure_date="2026-11-02",
                return_date=None,
                created_at=NOW,
            )
        )
        await session.commit()

    async with session_factory() as session:
        repository = HouseholdWatchRepository(session)
        watches = await repository.list_watches(HOUSEHOLD_A)

    assert [watch.id for watch in watches] == [WATCH_A]


@pytest.mark.anyio
async def test_repository_get_by_id_requires_matching_household() -> None:
    session_factory = await _session_factory()
    async with session_factory() as session:
        repository = HouseholdWatchRepository(session)
        await repository.add_watch(
            NewWatch(
                id=WATCH_A,
                household_id=HOUSEHOLD_A,
                owner_user_id=UUID("aaaaaaaa-0000-0000-0000-000000000001"),
                origin="WAW",
                destination="BCN",
                departure_date="2026-10-12",
                return_date=None,
                created_at=NOW,
            )
        )
        await session.commit()

    async with session_factory() as session:
        repository = HouseholdWatchRepository(session)
        visible = await repository.get_watch(HOUSEHOLD_A, WATCH_A)
        hidden = await repository.get_watch(HOUSEHOLD_B, WATCH_A)

    assert visible is not None
    assert hidden is None


async def _session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(mapper_registry.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)
