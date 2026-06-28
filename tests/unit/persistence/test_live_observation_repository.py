from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from flight_hunter.domain.money import Money
from flight_hunter.domain.observation import LiveObservation, ObservationStatus
from flight_hunter.domain.offers import FlightOffer, Freshness
from flight_hunter.domain.policy import UserActionGrant
from flight_hunter.persistence.models import mapper_registry
from flight_hunter.persistence.repositories import LiveObservationRepository

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
USER_A = UUID("11111111-1111-1111-1111-111111111111")
USER_B = UUID("22222222-2222-2222-2222-222222222222")
GRANT_ID = UUID("33333333-3333-3333-3333-333333333333")
OBSERVATION_ID = UUID("44444444-4444-4444-4444-444444444444")


def grant(**overrides: object) -> UserActionGrant:
    values: dict[str, object] = {
        "id": GRANT_ID,
        "user_id": USER_A,
        "provider_id": "demo_browser",
        "action_type": "live_observation",
        "request_fingerprint": "sha256:abc",
        "issued_at": NOW,
        "expires_at": NOW + timedelta(minutes=5),
        "source": "telegram_callback",
        "consumed_at": None,
    }
    values.update(overrides)
    return UserActionGrant(**values)


def observation(**overrides: object) -> LiveObservation:
    created_at = overrides.pop("created_at", NOW)
    if not isinstance(created_at, datetime):
        raise TypeError("created_at override must be a datetime")
    expires_at = overrides.pop("expires_at", NOW + timedelta(minutes=15))
    if not isinstance(expires_at, datetime):
        raise TypeError("expires_at override must be a datetime")
    offer = FlightOffer(
        provider_id="demo_browser",
        provider_offer_id=str(overrides.pop("provider_offer_id", "live-1")),
        origin="WAW",
        destination="BCN",
        departure_date="2026-10-12",
        return_date="2026-10-19",
        total_price=Money(minor_units=151200, currency="RUB"),
        passengers=2,
        observed_at=NOW,
        freshness=Freshness.LIVE_OBSERVED,
        requires_live_confirmation=True,
        baggage_summary=None,
    )
    values: dict[str, object] = {
        "observation_id": OBSERVATION_ID,
        "grant_id": GRANT_ID,
        "user_id": USER_A,
        "source_id": "demo_browser",
        "search_intent_hash": "sha256:abc",
        "status": ObservationStatus.SUCCEEDED,
        "created_at": created_at,
        "started_at": created_at,
        "completed_at": created_at,
        "expires_at": expires_at,
        "offers": (offer,),
        "error_code": None,
        "error_message": None,
    }
    values.update(overrides)
    return LiveObservation(**values)


@pytest.mark.anyio
async def test_repository_stores_grant_by_user_and_consumes_it_once() -> None:
    session_factory = await _session_factory()
    async with session_factory() as session:
        repository = LiveObservationRepository(session)
        await repository.add_grant(grant())
        await session.commit()

    async with session_factory() as session:
        repository = LiveObservationRepository(session)
        visible = await repository.get_grant(USER_A, GRANT_ID)
        hidden = await repository.get_grant(USER_B, GRANT_ID)
        first_consume = await repository.consume_grant(GRANT_ID, consumed_at=NOW)
        second_consume = await repository.consume_grant(GRANT_ID, consumed_at=NOW)
        await session.commit()

    assert visible is not None
    assert hidden is None
    assert first_consume is True
    assert second_consume is False


@pytest.mark.anyio
async def test_repository_stores_live_observation_with_user_scoped_lookup() -> None:
    session_factory = await _session_factory()
    async with session_factory() as session:
        repository = LiveObservationRepository(session)
        await repository.add_grant(grant(consumed_at=NOW))
        await repository.add_observation(observation())
        await session.commit()

    async with session_factory() as session:
        repository = LiveObservationRepository(session)
        visible = await repository.get_observation(USER_A, OBSERVATION_ID)
        hidden = await repository.get_observation(USER_B, OBSERVATION_ID)

    assert visible is not None
    assert visible.status == ObservationStatus.SUCCEEDED
    assert visible.offers[0].freshness == Freshness.LIVE_OBSERVED
    assert visible.offers[0].total_price == Money(minor_units=151200, currency="RUB")
    assert hidden is None


@pytest.mark.anyio
async def test_repository_cleans_expired_live_observation_state_preserving_active_results() -> None:
    session_factory = await _session_factory()
    active_grant_id = uuid4()
    expired_grant_id = uuid4()
    unused_grant_id = uuid4()
    active_observation_id = uuid4()
    expired_observation_id = uuid4()

    active_observation = observation(
        observation_id=active_observation_id,
        grant_id=active_grant_id,
        provider_offer_id="active-offer",
        expires_at=NOW + timedelta(minutes=10),
    )
    expired_created_at = NOW - timedelta(minutes=30)
    expired_observation = observation(
        observation_id=expired_observation_id,
        grant_id=expired_grant_id,
        provider_offer_id="expired-offer",
        created_at=expired_created_at,
        started_at=expired_created_at,
        completed_at=expired_created_at,
        expires_at=NOW - timedelta(seconds=1),
    )

    async with session_factory() as session:
        repository = LiveObservationRepository(session)
        await repository.add_grant(
            grant(
                id=active_grant_id,
                issued_at=NOW - timedelta(minutes=10),
                expires_at=NOW - timedelta(minutes=1),
                consumed_at=NOW - timedelta(minutes=2),
            )
        )
        await repository.add_grant(
            grant(
                id=expired_grant_id,
                issued_at=NOW - timedelta(minutes=30),
                expires_at=NOW - timedelta(minutes=20),
                consumed_at=NOW - timedelta(minutes=25),
            )
        )
        await repository.add_grant(
            grant(
                id=unused_grant_id,
                issued_at=NOW - timedelta(minutes=10),
                expires_at=NOW - timedelta(minutes=1),
            )
        )
        await repository.add_observation(active_observation)
        await repository.add_observation(expired_observation)
        await repository.record_idempotency(
            user_id=USER_A,
            idempotency_key="active-key",
            observation_id=active_observation_id,
            created_at=NOW,
        )
        await repository.record_idempotency(
            user_id=USER_A,
            idempotency_key="expired-key",
            observation_id=expired_observation_id,
            created_at=expired_created_at,
        )
        await session.commit()

    async with session_factory() as session:
        repository = LiveObservationRepository(session)
        result = await repository.cleanup_expired_live_observation_state(now=NOW)
        await session.commit()

    async with session_factory() as session:
        repository = LiveObservationRepository(session)
        active_after_cleanup = await repository.get_observation(USER_A, active_observation_id)
        expired_after_cleanup = await repository.get_observation(USER_A, expired_observation_id)
        active_idempotency = await repository.get_idempotent_observation_id(
            USER_A,
            "active-key",
        )
        expired_idempotency = await repository.get_idempotent_observation_id(
            USER_A,
            "expired-key",
        )
        expired_unused_grant = await repository.get_grant(USER_A, unused_grant_id)

    assert result.observations_deleted == 1
    assert result.offers_deleted == 1
    assert result.idempotency_deleted == 1
    assert result.grants_deleted == 3
    assert active_after_cleanup is not None
    assert expired_after_cleanup is None
    assert active_idempotency == active_observation_id
    assert expired_idempotency is None
    assert expired_unused_grant is None


async def _session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(mapper_registry.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)
