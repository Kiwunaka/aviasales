from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from flight_hunter.domain.policy import (
    DataKind,
    ExecutionContext,
    MergeScope,
    ProviderOperation,
    ProviderPolicy,
    UserActionGrant,
)
from flight_hunter.policy.guard import DenialCode, ProviderPolicyGuard

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
USER_ID = UUID("11111111-1111-1111-1111-111111111111")


def policy(**overrides: object) -> ProviderPolicy:
    values: dict[str, object] = {
        "provider_id": "test_provider",
        "policy_version": "2026-06-23",
        "terms_url": "https://example.test/terms",
        "terms_verified_at": NOW,
        "enabled": True,
        "credentials_present": True,
        "access_approved": True,
        "data_kind": DataKind.CACHED,
        "background_requests_allowed": True,
        "user_action_required": False,
        "merge_with_other_sources_allowed": True,
        "persist_raw_results_allowed": False,
        "persist_normalized_results_allowed": True,
        "booking_link_requires_click": True,
        "preload_booking_links_allowed": False,
        "server_side_only": True,
        "real_user_ip_required": False,
        "max_requests_per_minute": 30,
        "max_requests_per_hour_per_user_ip": None,
        "cache_ttl_seconds": 3600,
        "result_ttl_seconds": 86400,
        "max_concurrent_requests": 2,
        "supports_flexible_dates": True,
        "supports_nearby_airports": True,
        "supports_multi_city": False,
        "supports_one_way": True,
        "supports_round_trip": True,
        "supports_baggage": False,
        "supports_fare_rules": False,
        "notes": "test",
    }
    values.update(overrides)
    return ProviderPolicy(**values)


def grant(**overrides: object) -> UserActionGrant:
    values: dict[str, object] = {
        "id": UUID("22222222-2222-2222-2222-222222222222"),
        "user_id": USER_ID,
        "provider_id": "test_provider",
        "action_type": "live_refresh",
        "request_fingerprint": "sha256:abc",
        "issued_at": NOW - timedelta(minutes=1),
        "expires_at": NOW + timedelta(minutes=4),
        "source": "web_click",
        "consumed_at": None,
    }
    values.update(overrides)
    return UserActionGrant(**values)


def test_background_disallowed_provider_is_denied_for_scheduler() -> None:
    guard = ProviderPolicyGuard(clock=lambda: NOW)
    provider_policy = policy(background_requests_allowed=False)

    decision = guard.authorize(
        provider_policy,
        operation=ProviderOperation.SEARCH,
        context=ExecutionContext.SCHEDULER,
        request_fingerprint="sha256:abc",
    )

    assert not decision.allowed
    assert decision.code == DenialCode.BACKGROUND_NOT_ALLOWED


def test_user_action_provider_requires_matching_unconsumed_grant() -> None:
    guard = ProviderPolicyGuard(clock=lambda: NOW)
    provider_policy = policy(user_action_required=True)

    without_grant = guard.authorize(
        provider_policy,
        operation=ProviderOperation.SEARCH,
        context=ExecutionContext.WEB_USER_ACTION,
        request_fingerprint="sha256:abc",
    )
    with_grant = guard.authorize(
        provider_policy,
        operation=ProviderOperation.SEARCH,
        context=ExecutionContext.WEB_USER_ACTION,
        request_fingerprint="sha256:abc",
        user_action_grant=grant(),
    )
    second_use = guard.authorize(
        provider_policy,
        operation=ProviderOperation.SEARCH,
        context=ExecutionContext.WEB_USER_ACTION,
        request_fingerprint="sha256:abc",
        user_action_grant=with_grant.consumed_grant,
    )

    assert without_grant.code == DenialCode.USER_ACTION_GRANT_REQUIRED
    assert with_grant.allowed
    assert with_grant.consumed_grant is not None
    assert with_grant.consumed_grant.consumed_at == NOW
    assert second_use.code == DenialCode.USER_ACTION_GRANT_CONSUMED


def test_aviasales_search_policy_is_user_action_only_and_provider_isolated() -> None:
    provider_policy = ProviderPolicy.aviasales_search(
        terms_verified_at=NOW,
        credentials_present=False,
        access_approved=False,
        enabled=False,
    )

    assert provider_policy.data_kind == DataKind.LIVE
    assert provider_policy.merge_scope == MergeScope.PROVIDER_ISOLATED
    assert provider_policy.user_action_required
    assert not provider_policy.background_requests_allowed
    assert provider_policy.booking_link_requires_click
    assert not provider_policy.preload_booking_links_allowed
