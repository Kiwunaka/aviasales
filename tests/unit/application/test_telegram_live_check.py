from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from flight_hunter.application.live_observations import BrowserSourceCatalog, LiveObservationService
from flight_hunter.application.telegram_live_check import (
    TelegramLiveCheckCallback,
    TelegramLiveCheckService,
    build_live_check_callback_data,
)
from flight_hunter.domain.offers import Freshness, SearchIntent

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
USER_ID = UUID("11111111-1111-1111-1111-111111111111")


def intent() -> SearchIntent:
    return SearchIntent(
        origin="WAW",
        destination="BCN",
        departure_date="2026-10-12",
        return_date="2026-10-19",
        passengers=2,
        currency="RUB",
    )


def live_service() -> LiveObservationService:
    return LiveObservationService(
        catalog=BrowserSourceCatalog.demo(enabled=True, clock=lambda: NOW),
        clock=lambda: NOW,
        grant_ttl=timedelta(minutes=5),
    )


def test_callback_data_contains_only_source_and_alert_key() -> None:
    callback_data = build_live_check_callback_data(
        source_id="demo_browser",
        alert_key="alert-123",
    )

    assert callback_data == "live_check:demo_browser:alert-123"
    assert "grant" not in callback_data
    assert "token" not in callback_data
    assert "http" not in callback_data


def test_telegram_live_check_creates_observation_from_callback_grant() -> None:
    service = TelegramLiveCheckService(live_observation_service=live_service())

    result = service.handle_callback(
        TelegramLiveCheckCallback(
            callback_query_id="cb-1",
            telegram_user_id=12345,
            user_id=USER_ID,
            source_id="demo_browser",
            search_intent=intent(),
            alert_key="alert-123",
        )
    )

    assert result.accepted
    assert result.observation_id is not None
    assert result.status == "succeeded"
    assert result.offer is not None
    assert result.offer.freshness == Freshness.LIVE_OBSERVED


def test_telegram_callback_retry_is_idempotent_and_does_not_duplicate_alert_action() -> None:
    service = TelegramLiveCheckService(live_observation_service=live_service())
    callback = TelegramLiveCheckCallback(
        callback_query_id="cb-1",
        telegram_user_id=12345,
        user_id=USER_ID,
        source_id="demo_browser",
        search_intent=intent(),
        alert_key="alert-123",
    )

    first = service.handle_callback(callback)
    second = service.handle_callback(callback)

    assert first.accepted
    assert second.accepted
    assert second.idempotent_replay
    assert first.observation_id == second.observation_id
