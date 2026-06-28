from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from flight_hunter.application.live_observation_cleanup import LiveObservationCleanupService
from flight_hunter.domain.money import Money
from flight_hunter.domain.observation import LiveObservation, ObservationStatus
from flight_hunter.domain.offers import FlightOffer, Freshness
from flight_hunter.domain.policy import UserActionGrant
from flight_hunter.persistence.models import mapper_registry
from flight_hunter.persistence.repositories import LiveObservationRepository

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
USER_ID = UUID("11111111-1111-1111-1111-111111111111")


@pytest.mark.anyio
async def test_cleanup_service_commits_expired_live_observation_state() -> None:
    session_factory = await _session_factory()
    grant_id = uuid4()
    observation_id = uuid4()
    created_at = NOW - timedelta(minutes=30)

    async with session_factory() as session:
        repository = LiveObservationRepository(session)
        await repository.add_grant(
            UserActionGrant(
                id=grant_id,
                user_id=USER_ID,
                provider_id="demo_browser",
                action_type="live_observation",
                request_fingerprint="sha256:expired",
                issued_at=created_at,
                expires_at=NOW - timedelta(minutes=20),
                source="web_click",
                consumed_at=created_at,
            )
        )
        await repository.add_observation(
            LiveObservation(
                observation_id=observation_id,
                grant_id=grant_id,
                user_id=USER_ID,
                source_id="demo_browser",
                search_intent_hash="sha256:expired",
                status=ObservationStatus.SUCCEEDED,
                created_at=created_at,
                started_at=created_at,
                completed_at=created_at,
                expires_at=NOW - timedelta(seconds=1),
                offers=(
                    FlightOffer(
                        provider_id="demo_browser",
                        provider_offer_id="live-expired",
                        origin="WAW",
                        destination="BCN",
                        departure_date="2026-10-12",
                        return_date="2026-10-19",
                        total_price=Money(minor_units=151200, currency="RUB"),
                        passengers=2,
                        observed_at=created_at,
                        freshness=Freshness.LIVE_OBSERVED,
                        requires_live_confirmation=True,
                        baggage_summary=None,
                    ),
                ),
                error_code=None,
                error_message=None,
            )
        )
        await repository.record_idempotency(
            user_id=USER_ID,
            idempotency_key="expired-idem",
            observation_id=observation_id,
            created_at=created_at,
        )
        await session.commit()

    service = LiveObservationCleanupService(session_factory=session_factory, clock=lambda: NOW)
    result = await service.run_once()

    async with session_factory() as session:
        repository = LiveObservationRepository(session)
        observation = await repository.get_observation(USER_ID, observation_id)
        idempotency = await repository.get_idempotent_observation_id(USER_ID, "expired-idem")

    assert result.observations_deleted == 1
    assert result.offers_deleted == 1
    assert result.idempotency_deleted == 1
    assert result.grants_deleted == 1
    assert observation is None
    assert idempotency is None


async def _session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(mapper_registry.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)
