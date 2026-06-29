from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from flight_hunter.domain.money import Money
from flight_hunter.domain.offers import Freshness
from flight_hunter.domain.search_results import BrowserObservedOffer, Confidence
from flight_hunter.persistence.models import mapper_registry
from flight_hunter.persistence.repositories import BrowserObservedOfferRepository

NOW = datetime(2026, 6, 29, 16, 0, tzinfo=UTC)
HOUSEHOLD_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
HOUSEHOLD_B = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
USER_A = UUID("11111111-1111-1111-1111-111111111111")
USER_B = UUID("22222222-2222-2222-2222-222222222222")
SEARCH_ID = "sha256:observed-search"


@pytest.mark.anyio
async def test_browser_observed_offer_repository_is_household_user_and_search_scoped() -> None:
    session_factory = await _session_factory()
    async with session_factory() as session:
        repository = BrowserObservedOfferRepository(session)
        await repository.add_offer(
            household_id=HOUSEHOLD_A,
            user_id=USER_A,
            search_id=SEARCH_ID,
            offer=_offer(),
            expires_at=NOW + timedelta(minutes=5),
        )
        await session.commit()

    async with session_factory() as session:
        repository = BrowserObservedOfferRepository(session)
        visible = await repository.list_recent(
            household_id=HOUSEHOLD_A,
            user_id=USER_A,
            search_id=SEARCH_ID,
            now=NOW,
        )
        other_household = await repository.list_recent(
            household_id=HOUSEHOLD_B,
            user_id=USER_A,
            search_id=SEARCH_ID,
            now=NOW,
        )
        other_user = await repository.list_recent(
            household_id=HOUSEHOLD_A,
            user_id=USER_B,
            search_id=SEARCH_ID,
            now=NOW,
        )

    assert len(visible) == 1
    assert visible[0].total_price == Money(1_842_000, "RUB")
    assert visible[0].confidence == Confidence.MEDIUM
    assert visible[0].parser_version == "fixture-parser"
    assert visible[0].parser_warnings == ("baggage_unknown",)
    assert other_household == ()
    assert other_user == ()


@pytest.mark.anyio
async def test_browser_observed_offer_repository_hides_expired_results() -> None:
    session_factory = await _session_factory()
    async with session_factory() as session:
        repository = BrowserObservedOfferRepository(session)
        await repository.add_offer(
            household_id=HOUSEHOLD_A,
            user_id=USER_A,
            search_id=SEARCH_ID,
            offer=_offer(),
            expires_at=NOW - timedelta(seconds=1),
        )
        await session.commit()

    async with session_factory() as session:
        repository = BrowserObservedOfferRepository(session)
        visible = await repository.list_recent(
            household_id=HOUSEHOLD_A,
            user_id=USER_A,
            search_id=SEARCH_ID,
            now=NOW,
        )

    assert visible == ()


async def _session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(mapper_registry.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


def _offer() -> BrowserObservedOffer:
    return BrowserObservedOffer(
        observation_id=UUID("33333333-3333-3333-3333-333333333333"),
        source_id="tutu",
        source_name="Туту",
        provider_offer_id="tutu-card-1",
        origin="MOW",
        destination="IST",
        departure_date="2026-09-10",
        return_date="2026-09-20",
        total_price=Money(1_842_000, "RUB"),
        passengers=1,
        observed_at=NOW,
        final_url="https://www.tutu.ru/",
        display_url="www.tutu.ru",
        freshness=Freshness.BROWSER_OBSERVED,
        confidence=Confidence.MEDIUM,
        parser_version="fixture-parser",
        parser_warnings=("baggage_unknown",),
        airline_name="Turkish Airlines",
        airline_iata="TK",
        stops=1,
        baggage_summary="baggage unknown",
        seller_name="Туту",
    )
