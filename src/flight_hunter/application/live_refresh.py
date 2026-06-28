from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from flight_hunter.domain.policy import (
    ExecutionContext,
    ProviderOperation,
    ProviderPolicy,
    UserActionGrant,
    require_aware_datetime,
)
from flight_hunter.policy.guard import DenialCode, PolicyDecision, ProviderPolicyGuard


class LiveRefreshStatusCode(StrEnum):
    ALLOWED = "allowed"
    LIVE_REFRESH_TOO_SOON = "live_refresh_too_soon"
    POLICY_DENIED = "policy_denied"
    STATE_MISMATCH = "state_mismatch"


@dataclass(frozen=True, slots=True)
class LiveRefreshState:
    provider_id: str
    request_fingerprint: str
    last_refresh_at: datetime | None

    def __post_init__(self) -> None:
        if not self.provider_id:
            raise ValueError("provider_id is required")
        if not self.request_fingerprint:
            raise ValueError("request_fingerprint is required")
        if self.last_refresh_at is not None:
            require_aware_datetime(self.last_refresh_at, "last_refresh_at")


@dataclass(frozen=True, slots=True)
class LiveRefreshDecision:
    provider_id: str
    allowed: bool
    code: LiveRefreshStatusCode
    message: str
    next_allowed_at: datetime | None
    policy_decision: PolicyDecision


class LiveRefreshGate:
    def __init__(
        self,
        *,
        clock: Callable[[], datetime] | None = None,
        min_gap: timedelta = timedelta(minutes=10),
    ) -> None:
        if min_gap.total_seconds() < 0:
            raise ValueError("min_gap cannot be negative")
        self._clock = clock or (lambda: datetime.now(UTC))
        self._min_gap = min_gap
        self._guard = ProviderPolicyGuard(clock=self._clock)

    def authorize(
        self,
        policy: ProviderPolicy,
        *,
        context: ExecutionContext,
        request_fingerprint: str,
        user_action_grant: UserActionGrant | None,
        state: LiveRefreshState,
    ) -> LiveRefreshDecision:
        now = self._clock()
        require_aware_datetime(now, "now")
        state_matches = (
            state.provider_id == policy.provider_id
            and state.request_fingerprint == request_fingerprint
        )
        if not state_matches:
            return self._deny_without_consuming(
                policy=policy,
                code=LiveRefreshStatusCode.STATE_MISMATCH,
                message="live refresh state does not match this request",
                next_allowed_at=None,
            )

        next_allowed_at = self._next_allowed_at(state)
        if next_allowed_at is not None and now < next_allowed_at:
            return self._deny_without_consuming(
                policy=policy,
                code=LiveRefreshStatusCode.LIVE_REFRESH_TOO_SOON,
                message="live refresh is available after the configured minimum gap",
                next_allowed_at=next_allowed_at,
            )

        policy_decision = self._guard.authorize(
            policy,
            operation=ProviderOperation.LIVE_REFRESH,
            context=context,
            request_fingerprint=request_fingerprint,
            user_action_grant=user_action_grant,
        )
        if not policy_decision.allowed:
            return LiveRefreshDecision(
                provider_id=policy.provider_id,
                allowed=False,
                code=LiveRefreshStatusCode.POLICY_DENIED,
                message=policy_decision.message,
                next_allowed_at=None,
                policy_decision=policy_decision,
            )

        return LiveRefreshDecision(
            provider_id=policy.provider_id,
            allowed=True,
            code=LiveRefreshStatusCode.ALLOWED,
            message="live refresh allowed",
            next_allowed_at=None,
            policy_decision=policy_decision,
        )

    def _next_allowed_at(self, state: LiveRefreshState) -> datetime | None:
        if state.last_refresh_at is None:
            return None
        return state.last_refresh_at + self._min_gap

    @staticmethod
    def _deny_without_consuming(
        *,
        policy: ProviderPolicy,
        code: LiveRefreshStatusCode,
        message: str,
        next_allowed_at: datetime | None,
    ) -> LiveRefreshDecision:
        return LiveRefreshDecision(
            provider_id=policy.provider_id,
            allowed=False,
            code=code,
            message=message,
            next_allowed_at=next_allowed_at,
            policy_decision=PolicyDecision(
                provider_id=policy.provider_id,
                operation=ProviderOperation.LIVE_REFRESH,
                allowed=False,
                code=(
                    DenialCode.LIVE_REFRESH_TOO_SOON
                    if code == LiveRefreshStatusCode.LIVE_REFRESH_TOO_SOON
                    else DenialCode.STATE_MISMATCH
                ),
                message=message,
                merge_scope=policy.merge_scope,
                consumed_grant=None,
            ),
        )
