from __future__ import annotations

from datetime import UTC, datetime

import httpx2

from flight_hunter.domain.offers import Freshness, SearchIntent
from flight_hunter.domain.policy import ExecutionContext
from flight_hunter.providers.aviasales_data.adapter import AviasalesDataAdapter
from flight_hunter.providers.aviasales_data.client import AviasalesDataClient

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)


def test_adapter_checks_policy_before_http_call_when_disabled() -> None:
    calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        return httpx2.Response(200, json={"success": True, "data": [], "error": None})

    adapter = AviasalesDataAdapter(
        client=AviasalesDataClient(
            token="test-token",
            http_client=httpx2.Client(
                transport=httpx2.MockTransport(handler),
                base_url="https://api.travelpayouts.com",
            ),
            clock=lambda: NOW,
        ),
        enabled=False,
        credentials_present=True,
        clock=lambda: NOW,
    )

    offers = adapter.search(
        SearchIntent(
            origin="WAW",
            destination="BCN",
            departure_date="2026-10-12",
            return_date=None,
            passengers=1,
            currency="PLN",
        ),
        request_fingerprint="sha256:test",
        context=ExecutionContext.WEB_USER_ACTION,
    )

    assert offers == ()
    assert calls == 0


def test_adapter_returns_cached_offers_when_enabled_and_credentials_present() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json={
                "success": True,
                "data": [
                    {
                        "origin": "WAW",
                        "destination": "BCN",
                        "price": 512,
                        "departure_at": "2026-10-12T07:00:00+02:00",
                        "return_at": None,
                        "link": "/search/WAW1210BCN",
                    }
                ],
                "error": None,
            },
        )

    adapter = AviasalesDataAdapter(
        client=AviasalesDataClient(
            token="test-token",
            http_client=httpx2.Client(
                transport=httpx2.MockTransport(handler),
                base_url="https://api.travelpayouts.com",
            ),
            clock=lambda: NOW,
        ),
        enabled=True,
        credentials_present=True,
        clock=lambda: NOW,
    )

    offers = adapter.search(
        SearchIntent(
            origin="WAW",
            destination="BCN",
            departure_date="2026-10-12",
            return_date=None,
            passengers=1,
            currency="PLN",
        ),
        request_fingerprint="sha256:test",
        context=ExecutionContext.SCHEDULER,
    )

    assert len(offers) == 1
    assert offers[0].freshness == Freshness.CACHED
    assert offers[0].requires_live_confirmation


def test_adapter_does_not_call_data_api_for_child_or_infant_pricing() -> None:
    calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        return httpx2.Response(200, json={"success": True, "data": [], "error": None})

    adapter = AviasalesDataAdapter(
        client=AviasalesDataClient(
            token="test-token",
            http_client=httpx2.Client(
                transport=httpx2.MockTransport(handler),
                base_url="https://api.travelpayouts.com",
            ),
            clock=lambda: NOW,
        ),
        enabled=True,
        credentials_present=True,
        clock=lambda: NOW,
    )

    offers = adapter.search(
        SearchIntent(
            origin="WAW",
            destination="BCN",
            departure_date="2026-10-12",
            return_date="2026-10-19",
            passengers=3,
            currency="RUB",
            adults=2,
            children=1,
            infants=0,
        ),
        request_fingerprint="sha256:test",
        context=ExecutionContext.WEB_USER_ACTION,
    )

    assert offers == ()
    assert calls == 0
