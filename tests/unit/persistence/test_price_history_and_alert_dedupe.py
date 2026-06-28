from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from flight_hunter.domain.money import Money
from flight_hunter.domain.offers import Freshness
from flight_hunter.notifications.alerts import (
    AlertEvaluationState,
    AlertEvaluator,
    AlertReason,
    PriceObservation,
)
from flight_hunter.persistence.models import mapper_registry
from flight_hunter.persistence.repositories import (
    AlertDedupeRepository,
    NewPriceSnapshot,
    PriceSnapshotRepository,
)

HOUSEHOLD_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
HOUSEHOLD_B = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
WATCH_A = UUID("11111111-1111-1111-1111-111111111111")
WATCH_B = UUID("22222222-2222-2222-2222-222222222222")
SNAPSHOT_1 = UUID("33333333-3333-3333-3333-333333333333")
SNAPSHOT_2 = UUID("44444444-4444-4444-4444-444444444444")
NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)


@pytest.mark.anyio
async def test_price_snapshots_are_append_only_and_household_scoped() -> None:
    session_factory = await _session_factory()
    async with session_factory() as session:
        repository = PriceSnapshotRepository(session)
        await repository.add_snapshot(
            _snapshot(
                id=SNAPSHOT_1,
                household_id=HOUSEHOLD_A,
                watch_id=WATCH_A,
                amount_minor=100_000,
                observed_at=NOW,
            )
        )
        await repository.add_snapshot(
            _snapshot(
                id=SNAPSHOT_2,
                household_id=HOUSEHOLD_A,
                watch_id=WATCH_A,
                amount_minor=88_000,
                observed_at=NOW + timedelta(hours=1),
            )
        )
        await repository.add_snapshot(
            _snapshot(
                id=UUID("55555555-5555-5555-5555-555555555555"),
                household_id=HOUSEHOLD_B,
                watch_id=WATCH_B,
                amount_minor=1,
                observed_at=NOW,
            )
        )
        await session.commit()

    async with session_factory() as session:
        repository = PriceSnapshotRepository(session)
        visible = await repository.list_history(HOUSEHOLD_A, WATCH_A)
        hidden = await repository.list_history(HOUSEHOLD_B, WATCH_A)

    assert [snapshot.id for snapshot in visible] == [SNAPSHOT_1, SNAPSHOT_2]
    assert [snapshot.price.minor_units for snapshot in visible] == [100_000, 88_000]
    assert visible[0].observed_at.tzinfo is not None
    assert hidden == ()


@pytest.mark.anyio
async def test_alert_dedupe_state_is_durable() -> None:
    session_factory = await _session_factory()
    evaluator = AlertEvaluator(drop_threshold_percent=10, cooldown=timedelta(hours=6))
    result = evaluator.evaluate(
        previous_best=PriceObservation(
            watch_id=str(WATCH_A),
            itinerary_fingerprint="route-1",
            observed_at=NOW - timedelta(hours=1),
            price=Money(100_000, "PLN"),
        ),
        current=PriceObservation(
            watch_id=str(WATCH_A),
            itinerary_fingerprint="route-1",
            observed_at=NOW,
            price=Money(88_000, "PLN"),
        ),
        state=AlertEvaluationState.empty(),
    )
    assert result.alert is not None
    assert result.alert.reason == AlertReason.PRICE_DROP

    async with session_factory() as session:
        repository = AlertDedupeRepository(session)
        inserted = await repository.record_alert(HOUSEHOLD_A, result.alert)
        inserted_again = await repository.record_alert(HOUSEHOLD_A, result.alert)
        await session.commit()

    async with session_factory() as session:
        repository = AlertDedupeRepository(session)
        state = await repository.load_state(HOUSEHOLD_A, WATCH_A)
        hidden = await repository.load_state(HOUSEHOLD_B, WATCH_A)

    assert inserted
    assert not inserted_again
    assert result.alert.dedupe_key in state.sent_dedupe_keys
    assert state.last_sent_at_by_bucket[str(WATCH_A) + ":route-1:price_drop"] == NOW
    assert hidden == AlertEvaluationState.empty()


def _snapshot(
    *,
    id: UUID,
    household_id: UUID,
    watch_id: UUID,
    amount_minor: int,
    observed_at: datetime,
) -> NewPriceSnapshot:
    return NewPriceSnapshot(
        id=id,
        household_id=household_id,
        watch_id=watch_id,
        provider_id="fake",
        itinerary_fingerprint="route-1",
        observed_at=observed_at,
        price=Money(amount_minor, "PLN"),
        freshness=Freshness.CACHED,
        requires_live_confirmation=True,
    )


async def _session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(mapper_registry.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)
