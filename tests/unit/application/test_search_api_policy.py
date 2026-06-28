from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from flight_hunter.application.search_api_policy import (
    SearchApiBookingAction,
    SearchApiPolicyGateway,
)
from flight_hunter.domain.policy import (
    ExecutionContext,
    MergeScope,
    ProviderOperation,
    ProviderPolicy,
    UserActionGrant,
)
from flight_hunter.policy.guard import DenialCode

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
USER_ID = UUID("11111111-1111-1111-1111-111111111111")


def search_policy(*, enabled: bool = True) -> ProviderPolicy:
    return ProviderPolicy.aviasales_search(
        terms_verified_at=NOW,
        credentials_present=True,
        access_approved=True,
        enabled=enabled,
    )


def grant(**overrides: object) -> UserActionGrant:
    values: dict[str, object] = {
        "id": UUID("22222222-2222-2222-2222-222222222222"),
        "user_id": USER_ID,
        "provider_id": "aviasales_search",
        "action_type": "search_api",
        "request_fingerprint": "sha256:abc",
        "issued_at": NOW - timedelta(minutes=1),
        "expires_at": NOW + timedelta(minutes=4),
        "source": "web_click",
        "consumed_at": None,
    }
    values.update(overrides)
    return UserActionGrant(**values)


def test_search_api_requires_user_action_and_provider_isolated_results() -> None:
    gateway = SearchApiPolicyGateway(clock=lambda: NOW)

    decision = gateway.authorize_search(
        search_policy(),
        context=ExecutionContext.WEB_USER_ACTION,
        request_fingerprint="sha256:abc",
        user_action_grant=grant(),
    )

    assert decision.allowed
    assert decision.operation == ProviderOperation.SEARCH
    assert decision.merge_scope == MergeScope.PROVIDER_ISOLATED
    assert decision.consumed_grant is not None


def test_search_api_denies_scheduler_execution_even_with_grant() -> None:
    gateway = SearchApiPolicyGateway(clock=lambda: NOW)

    decision = gateway.authorize_search(
        search_policy(),
        context=ExecutionContext.SCHEDULER,
        request_fingerprint="sha256:abc",
        user_action_grant=grant(),
    )

    assert not decision.allowed
    assert decision.code == DenialCode.BACKGROUND_NOT_ALLOWED
    assert decision.consumed_grant is None


def test_search_api_disabled_flag_fails_closed() -> None:
    gateway = SearchApiPolicyGateway(clock=lambda: NOW)

    decision = gateway.authorize_search(
        search_policy(enabled=False),
        context=ExecutionContext.WEB_USER_ACTION,
        request_fingerprint="sha256:abc",
        user_action_grant=grant(),
    )

    assert not decision.allowed
    assert decision.code == DenialCode.PROVIDER_DISABLED


def test_booking_action_descriptor_is_created_only_after_click_grant() -> None:
    gateway = SearchApiPolicyGateway(clock=lambda: NOW)

    denied = gateway.create_booking_action(
        search_policy(),
        provider_offer_id="offer_1",
        request_fingerprint="sha256:abc",
        user_action_grant=None,
    )
    allowed = gateway.create_booking_action(
        search_policy(),
        provider_offer_id="offer_1",
        request_fingerprint="sha256:abc",
        user_action_grant=grant(action_type="booking_action"),
    )

    assert not denied.allowed
    assert denied.code == DenialCode.USER_ACTION_GRANT_REQUIRED
    assert allowed.allowed
    assert allowed.action == SearchApiBookingAction(
        provider_id="aviasales_search",
        provider_offer_id="offer_1",
        kind="click_time_redirect",
        preload_allowed=False,
    )
