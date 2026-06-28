from __future__ import annotations

from datetime import UTC, datetime

import httpx2
import pytest

from flight_hunter.providers.aviasales_data.client import (
    AviasalesDataClient,
    AviasalesDataRateLimited,
    PricesForDatesQuery,
)


def test_prices_for_dates_sends_token_in_header_and_safe_query_params() -> None:
    captured_request: httpx2.Request | None = None

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal captured_request
        captured_request = request
        return httpx2.Response(
            200,
            json={
                "success": True,
                "data": [],
                "error": None,
            },
        )

    client = AviasalesDataClient(
        token="test-token",
        http_client=httpx2.Client(
            transport=httpx2.MockTransport(handler),
            base_url="https://api.travelpayouts.com",
        ),
    )

    client.prices_for_dates(
        PricesForDatesQuery(
            origin="WAW",
            destination="BCN",
            departure_at="2026-10-12",
            return_at="2026-10-19",
            currency="PLN",
            market="pl",
            one_way=False,
            direct=False,
            limit=30,
            page=1,
        )
    )

    assert captured_request is not None
    assert captured_request.url.path == "/aviasales/v3/prices_for_dates"
    assert captured_request.headers["x-access-token"] == "test-token"
    assert "token" not in str(captured_request.url)
    assert captured_request.url.params["origin"] == "WAW"
    assert captured_request.url.params["destination"] == "BCN"
    assert captured_request.url.params["departure_at"] == "2026-10-12"
    assert captured_request.url.params["return_at"] == "2026-10-19"
    assert captured_request.url.params["cy"] == "pln"
    assert captured_request.url.params["one_way"] == "false"


def test_prices_for_dates_raises_rate_limited_with_retry_after() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(429, headers={"Retry-After": "60"}, json={"error": "rate limit"})

    client = AviasalesDataClient(
        token="test-token",
        http_client=httpx2.Client(
            transport=httpx2.MockTransport(handler),
            base_url="https://api.travelpayouts.com",
        ),
    )

    with pytest.raises(AviasalesDataRateLimited) as exc_info:
        client.prices_for_dates(
            PricesForDatesQuery(
                origin="WAW",
                destination="BCN",
                departure_at="2026-10-12",
                return_at=None,
                currency="PLN",
                market="pl",
                one_way=True,
                direct=False,
                limit=30,
                page=1,
            )
        )

    assert exc_info.value.retry_after_seconds == 60


def test_prices_for_dates_maps_successful_response() -> None:
    received_at = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json={
                "success": True,
                "data": [
                    {
                        "origin": "WAW",
                        "destination": "BCN",
                        "origin_airport": "WAW",
                        "destination_airport": "BCN",
                        "price": 512,
                        "airline": "LO",
                        "flight_number": "437",
                        "departure_at": "2026-10-12T07:00:00+02:00",
                        "return_at": "2026-10-19T14:30:00+02:00",
                        "transfers": 0,
                        "return_transfers": 1,
                        "duration": 340,
                        "link": "/search/WAW1210BCN1910",
                    }
                ],
                "error": None,
            },
        )

    client = AviasalesDataClient(
        token="test-token",
        http_client=httpx2.Client(
            transport=httpx2.MockTransport(handler),
            base_url="https://api.travelpayouts.com",
        ),
        clock=lambda: received_at,
    )

    response = client.prices_for_dates(
        PricesForDatesQuery(
            origin="WAW",
            destination="BCN",
            departure_at="2026-10-12",
            return_at="2026-10-19",
            currency="PLN",
            market="pl",
            one_way=False,
            direct=False,
            limit=30,
            page=1,
        )
    )

    assert response.received_at == received_at
    assert len(response.items) == 1
    assert response.items[0].price_minor_units == 51200
    assert response.items[0].departure_date == "2026-10-12"
    assert response.items[0].return_date == "2026-10-19"
