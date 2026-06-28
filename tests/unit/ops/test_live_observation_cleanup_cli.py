from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from flight_hunter.domain.money import Money
from flight_hunter.domain.observation import LiveObservation, ObservationStatus
from flight_hunter.domain.offers import FlightOffer, Freshness
from flight_hunter.domain.policy import UserActionGrant
from flight_hunter.ops.live_observation_cleanup import (
    cleanup_live_observation_state,
    render_cleanup_result,
)
from flight_hunter.persistence.models import mapper_registry
from flight_hunter.persistence.repositories import LiveObservationRepository

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
USER_ID = UUID("11111111-1111-1111-1111-111111111111")


@pytest.mark.anyio
async def test_cleanup_command_reports_missing_local_sqlite_database(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'missing.db').as_posix()}"

    result = await cleanup_live_observation_state(
        database_url=database_url,
        clock=lambda: NOW,
    )

    assert result.ok is False
    assert result.code == "database_missing"
    assert result.observations_deleted == 0


@pytest.mark.anyio
async def test_cleanup_command_supports_dry_run_and_commit(tmp_path: Path) -> None:
    db_path = tmp_path / "flight_hunter_dev.db"
    observation_id = uuid4()
    await _seed_expired_observation(db_path, observation_id=observation_id)
    database_url = f"sqlite+aiosqlite:///{db_path.as_posix()}"

    dry_run = await cleanup_live_observation_state(
        database_url=database_url,
        dry_run=True,
        clock=lambda: NOW,
    )
    still_present_after_dry_run = await _observation_exists(db_path, observation_id)

    committed = await cleanup_live_observation_state(
        database_url=database_url,
        dry_run=False,
        clock=lambda: NOW,
    )
    present_after_commit = await _observation_exists(db_path, observation_id)
    output = render_cleanup_result(committed)
    payload = json.loads(output)

    assert dry_run.ok is True
    assert dry_run.dry_run is True
    assert dry_run.observations_deleted == 1
    assert dry_run.offers_deleted == 1
    assert dry_run.idempotency_deleted == 1
    assert dry_run.grants_deleted == 1
    assert still_present_after_dry_run is True
    assert committed.ok is True
    assert committed.dry_run is False
    assert committed.observations_deleted == 1
    assert present_after_commit is False
    assert payload["code"] == "ok"
    assert "11111111-1111-1111-1111-111111111111" not in output
    assert "expired-idem" not in output


async def _seed_expired_observation(db_path: Path, *, observation_id: UUID) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path.as_posix()}")
    async with engine.begin() as connection:
        await connection.run_sync(mapper_registry.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    grant_id = uuid4()
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
    await engine.dispose()


async def _observation_exists(db_path: Path, observation_id: UUID) -> bool:
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path.as_posix()}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        repository = LiveObservationRepository(session)
        observation = await repository.get_observation(USER_ID, observation_id)
    await engine.dispose()
    return observation is not None
