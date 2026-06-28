from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from flight_hunter.application.live_refresh import (
    LiveRefreshGate,
    LiveRefreshState,
    LiveRefreshStatusCode,
)
from flight_hunter.domain.policy import (
    DataKind,
    ExecutionContext,
    ProviderOperation,
    ProviderPolicy,
    UserActionGrant,
)
from flight_hunter.policy.guard import DenialCode

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
USER_ID = UUID("11111111-1111-1111-1111-111111111111")


def live_policy(**overrides: object) -> ProviderPolicy:
    values: dict[str, object] = {
        "provider_id": "live_provider",
        "policy_version": "2026-06-23",
        "terms_url": "https://example.test/live",
        "terms_verified_at": NOW,
        "enabled": True,
        "credentials_present": True,
        "access_approved": True,
        "data_kind": DataKind.LIVE,
        "background_requests_allowed": False,
        "user_action_required": True,
        "merge_with_other_sources_allowed": False,
        "persist_raw_results_allowed": False,
        "persist_normalized_results_allowed": True,
        "booking_link_requires_click": True,
        "preload_booking_links_allowed": False,
        "server_side_only": True,
        "real_user_ip_required": True,
        "max_requests_per_minute": None,
        "max_requests_per_hour_per_user_ip": 100,
        "cache_ttl_seconds": 0,
        "result_ttl_seconds": 900,
        "max_concurrent_requests": 1,
        "supports_flexible_dates": False,
        "supports_nearby_airports": False,
        "supports_multi_city": True,
        "supports_one_way": True,
        "supports_round_trip": True,
        "supports_baggage": True,
        "supports_fare_rules": True,
        "notes": "test live provider",
    }
    values.update(overrides)
    return ProviderPolicy(**values)


def grant(**overrides: object) -> UserActionGrant:
    values: dict[str, object] = {
        "id": UUID("22222222-2222-2222-2222-222222222222"),
        "user_id": USER_ID,
        "provider_id": "live_provider",
        "action_type": "live_refresh",
        "request_fingerprint": "sha256:abc",
        "issued_at": NOW - timedelta(minutes=1),
        "expires_at": NOW + timedelta(minutes=4),
        "source": "web_click",
        "consumed_at": None,
    }
    values.update(overrides)
    return UserActionGrant(**values)


def test_first_live_refresh_is_allowed_with_real_user_grant() -> None:
    gate = LiveRefreshGate(clock=lambda: NOW, min_gap=timedelta(minutes=10))

    decision = gate.authorize(
        live_policy(),
        context=ExecutionContext.WEB_USER_ACTION,
        request_fingerprint="sha256:abc",
        user_action_grant=grant(),
        state=LiveRefreshState(
            provider_id="live_provider",
            request_fingerprint="sha256:abc",
            last_refresh_at=None,
        ),
    )

    assert decision.allowed
    assert decision.code == LiveRefreshStatusCode.ALLOWED
    assert decision.next_allowed_at is None
    assert decision.policy_decision.operation == ProviderOperation.LIVE_REFRESH
    assert decision.policy_decision.consumed_grant is not None


def test_live_refresh_is_blocked_until_ten_minute_gap_passes() -> None:
    gate = LiveRefreshGate(clock=lambda: NOW, min_gap=timedelta(minutes=10))

    decision = gate.authorize(
        live_policy(),
        context=ExecutionContext.WEB_USER_ACTION,
        request_fingerprint="sha256:abc",
        user_action_grant=grant(),
        state=LiveRefreshState(
            provider_id="live_provider",
            request_fingerprint="sha256:abc",
            last_refresh_at=NOW - timedelta(minutes=9, seconds=59),
        ),
    )

    assert not decision.allowed
    assert decision.code == LiveRefreshStatusCode.LIVE_REFRESH_TOO_SOON
    assert decision.next_allowed_at == NOW + timedelta(seconds=1)
    assert decision.policy_decision.consumed_grant is None


def test_live_refresh_is_allowed_at_exact_ten_minute_gap() -> None:
    gate = LiveRefreshGate(clock=lambda: NOW, min_gap=timedelta(minutes=10))

    decision = gate.authorize(
        live_policy(),
        context=ExecutionContext.WEB_USER_ACTION,
        request_fingerprint="sha256:abc",
        user_action_grant=grant(),
        state=LiveRefreshState(
            provider_id="live_provider",
            request_fingerprint="sha256:abc",
            last_refresh_at=NOW - timedelta(minutes=10),
        ),
    )

    assert decision.allowed
    assert decision.code == LiveRefreshStatusCode.ALLOWED


def test_live_refresh_still_requires_provider_policy_grant() -> None:
    gate = LiveRefreshGate(clock=lambda: NOW, min_gap=timedelta(minutes=10))

    decision = gate.authorize(
        live_policy(),
        context=ExecutionContext.WEB_USER_ACTION,
        request_fingerprint="sha256:abc",
        user_action_grant=None,
        state=LiveRefreshState(
            provider_id="live_provider",
            request_fingerprint="sha256:abc",
            last_refresh_at=None,
        ),
    )

    assert not decision.allowed
    assert decision.code == LiveRefreshStatusCode.POLICY_DENIED
    assert decision.policy_decision.code == DenialCode.USER_ACTION_GRANT_REQUIRED
