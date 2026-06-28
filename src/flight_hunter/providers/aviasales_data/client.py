from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx2


@dataclass(frozen=True, slots=True)
class PricesForDatesQuery:
    origin: str
    destination: str
    departure_at: str
    return_at: str | None
    currency: str
    market: str
    one_way: bool
    direct: bool
    limit: int
    page: int


@dataclass(frozen=True, slots=True)
class AviasalesDataItem:
    origin: str
    destination: str
    origin_airport: str | None
    destination_airport: str | None
    price_minor_units: int
    currency: str
    departure_date: str
    return_date: str | None
    airline: str | None
    flight_number: str | None
    link_path: str | None


@dataclass(frozen=True, slots=True)
class AviasalesDataResponse:
    received_at: datetime
    items: tuple[AviasalesDataItem, ...]


class AviasalesDataError(RuntimeError):
    pass


class AviasalesDataRateLimited(AviasalesDataError):
    def __init__(self, *, retry_after_seconds: int | None) -> None:
        super().__init__("aviasales_data_rate_limited")
        self.retry_after_seconds = retry_after_seconds


class AviasalesDataClient:
    def __init__(
        self,
        *,
        token: str,
        http_client: httpx2.Client | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not token:
            raise ValueError("token is required")
        self._token = token
        self._client = http_client or httpx2.Client(
            base_url="https://api.travelpayouts.com",
            timeout=10.0,
            headers={"Accept-Encoding": "gzip, deflate"},
        )
        self._clock = clock or (lambda: datetime.now(UTC))

    def prices_for_dates(self, query: PricesForDatesQuery) -> AviasalesDataResponse:
        response = self._client.get(
            "/aviasales/v3/prices_for_dates",
            params=_query_params(query),
            headers={"X-Access-Token": self._token},
        )
        if response.status_code == 429:
            raise AviasalesDataRateLimited(
                retry_after_seconds=_parse_retry_after(response.headers.get("Retry-After"))
            )
        if response.status_code >= 400:
            raise AviasalesDataError(f"aviasales_data_http_{response.status_code}")

        payload = response.json()
        if not isinstance(payload, dict):
            raise AviasalesDataError("aviasales_data_invalid_payload")
        if payload.get("success") is not True:
            raise AviasalesDataError("aviasales_data_unsuccessful")

        raw_items = payload.get("data")
        if not isinstance(raw_items, list):
            raise AviasalesDataError("aviasales_data_invalid_data")

        received_at = self._clock()
        return AviasalesDataResponse(
            received_at=received_at,
            items=tuple(_parse_item(item, query.currency) for item in raw_items),
        )


def _query_params(query: PricesForDatesQuery) -> dict[str, str | int]:
    params: dict[str, str | int] = {
        "origin": query.origin.upper(),
        "destination": query.destination.upper(),
        "departure_at": query.departure_at,
        "one_way": _bool_param(query.one_way),
        "direct": _bool_param(query.direct),
        "market": query.market.lower(),
        "cy": query.currency.lower(),
        "limit": query.limit,
        "page": query.page,
        "sorting": "price",
        "unique": "false",
    }
    if query.return_at is not None:
        params["return_at"] = query.return_at
    return params


def _parse_item(raw: Any, currency: str) -> AviasalesDataItem:
    if not isinstance(raw, dict):
        raise AviasalesDataError("aviasales_data_invalid_item")
    price = raw.get("price")
    if type(price) is not int:
        raise AviasalesDataError("aviasales_data_missing_price")
    departure_at = _required_string(raw.get("departure_at"), "departure_at")
    return_at = raw.get("return_at")
    if return_at is not None and not isinstance(return_at, str):
        return_at = None

    return AviasalesDataItem(
        origin=_required_string(raw.get("origin"), "origin").upper(),
        destination=_required_string(raw.get("destination"), "destination").upper(),
        origin_airport=_optional_upper(raw.get("origin_airport")),
        destination_airport=_optional_upper(raw.get("destination_airport")),
        price_minor_units=price * 100,
        currency=currency.upper(),
        departure_date=departure_at[:10],
        return_date=return_at[:10] if isinstance(return_at, str) else None,
        airline=_optional_upper(raw.get("airline")),
        flight_number=_optional_string(raw.get("flight_number")),
        link_path=_optional_string(raw.get("link")),
    )


def stable_item_id(item: AviasalesDataItem) -> str:
    raw = "|".join(
        (
            item.origin,
            item.destination,
            item.departure_date,
            item.return_date or "",
            str(item.price_minor_units),
            item.currency,
            item.airline or "",
            item.flight_number or "",
        )
    )
    return "aviasales_data:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _required_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise AviasalesDataError(f"aviasales_data_missing_{field_name}")
    return value


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _optional_upper(value: Any) -> str | None:
    return value.upper() if isinstance(value, str) and value else None


def _bool_param(value: bool) -> str:
    return "true" if value else "false"


def _parse_retry_after(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        retry_after = int(value)
    except ValueError:
        return None
    return retry_after if retry_after >= 0 else None
