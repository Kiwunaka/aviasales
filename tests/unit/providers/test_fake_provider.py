from __future__ import annotations

from datetime import UTC, datetime

from flight_hunter.domain.money import Money
from flight_hunter.domain.offers import Freshness, SearchIntent
from flight_hunter.domain.policy import ExecutionContext, ProviderOperation
from flight_hunter.providers.fake import FakeFlightProvider

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)


def test_fake_provider_policy_is_mergeable_background_demo_source() -> None:
    provider = FakeFlightProvider(clock=lambda: NOW)

    decision = provider.authorize(
        operation=ProviderOperation.SEARCH,
        context=ExecutionContext.SCHEDULER,
        request_fingerprint="sha256:demo",
    )

    assert decision.allowed
    assert provider.policy.provider_id == "fake"
    assert provider.policy.background_requests_allowed
    assert provider.policy.merge_with_other_sources_allowed


def test_fake_provider_returns_deterministic_cached_demo_offer() -> None:
    provider = FakeFlightProvider(clock=lambda: NOW)
    intent = SearchIntent(
        origin="WAW",
        destination="BCN",
        departure_date="2026-10-12",
        return_date="2026-10-19",
        passengers=2,
        currency="PLN",
    )

    first = provider.search(intent, request_fingerprint="sha256:demo")
    second = provider.search(intent, request_fingerprint="sha256:demo")

    assert first == second
    assert first[0].provider_id == "fake"
    assert first[0].observed_at == NOW
    assert first[0].freshness == Freshness.CACHED
    assert first[0].total_price == Money(159800, "PLN")
    assert first[0].passengers == 2
    assert first[0].requires_live_confirmation
