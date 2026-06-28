from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from flight_hunter.domain.policy import (
    ExecutionContext,
    ProviderOperation,
    ProviderPolicy,
    UserActionGrant,
)
from flight_hunter.policy.guard import DenialCode, PolicyDecision, ProviderPolicyGuard


@dataclass(frozen=True, slots=True)
class SearchApiBookingAction:
    provider_id: str
    provider_offer_id: str
    kind: str
    preload_allowed: bool


@dataclass(frozen=True, slots=True)
class SearchApiBookingDecision:
    allowed: bool
    code: DenialCode
    message: str
    action: SearchApiBookingAction | None
    consumed_grant: UserActionGrant | None


class SearchApiPolicyGateway:
    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))
        self._guard = ProviderPolicyGuard(clock=self._clock)

    def authorize_search(
        self,
        policy: ProviderPolicy,
        *,
        context: ExecutionContext,
        request_fingerprint: str,
        user_action_grant: UserActionGrant | None,
    ) -> PolicyDecision:
        return self._guard.authorize(
            policy,
            operation=ProviderOperation.SEARCH,
            context=context,
            request_fingerprint=request_fingerprint,
            user_action_grant=user_action_grant,
        )

    def create_booking_action(
        self,
        policy: ProviderPolicy,
        *,
        provider_offer_id: str,
        request_fingerprint: str,
        user_action_grant: UserActionGrant | None,
    ) -> SearchApiBookingDecision:
        decision = self._guard.authorize(
            policy,
            operation=ProviderOperation.BOOKING_ACTION,
            context=ExecutionContext.WEB_USER_ACTION,
            request_fingerprint=request_fingerprint,
            user_action_grant=user_action_grant,
        )
        if not decision.allowed:
            return SearchApiBookingDecision(
                allowed=False,
                code=decision.code,
                message=decision.message,
                action=None,
                consumed_grant=decision.consumed_grant,
            )

        return SearchApiBookingDecision(
            allowed=True,
            code=decision.code,
            message="booking action descriptor created after user click",
            action=SearchApiBookingAction(
                provider_id=policy.provider_id,
                provider_offer_id=provider_offer_id,
                kind="click_time_redirect",
                preload_allowed=policy.preload_booking_links_allowed,
            ),
            consumed_grant=decision.consumed_grant,
        )
