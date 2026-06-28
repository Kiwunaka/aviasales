from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from flight_hunter.domain.policy import (
    ExecutionContext,
    MergeScope,
    ProviderOperation,
    ProviderPolicy,
    UserActionGrant,
)


class DenialCode(StrEnum):
    ALLOWED = "allowed"
    ACCESS_NOT_APPROVED = "access_not_approved"
    BACKGROUND_NOT_ALLOWED = "background_not_allowed"
    CREDENTIALS_MISSING = "credentials_missing"
    LIVE_REFRESH_TOO_SOON = "live_refresh_too_soon"
    PROVIDER_DISABLED = "provider_disabled"
    STATE_MISMATCH = "state_mismatch"
    USER_ACTION_GRANT_CONSUMED = "user_action_grant_consumed"
    USER_ACTION_GRANT_EXPIRED = "user_action_grant_expired"
    USER_ACTION_GRANT_FINGERPRINT_MISMATCH = "user_action_grant_fingerprint_mismatch"
    USER_ACTION_GRANT_PROVIDER_MISMATCH = "user_action_grant_provider_mismatch"
    USER_ACTION_GRANT_REQUIRED = "user_action_grant_required"


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    provider_id: str
    operation: ProviderOperation
    allowed: bool
    code: DenialCode
    message: str
    merge_scope: MergeScope
    consumed_grant: UserActionGrant | None = None


class ProviderPolicyGuard:
    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))

    def authorize(
        self,
        policy: ProviderPolicy,
        *,
        operation: ProviderOperation,
        context: ExecutionContext,
        request_fingerprint: str,
        user_action_grant: UserActionGrant | None = None,
    ) -> PolicyDecision:
        if not policy.enabled:
            return self._deny(policy, operation, DenialCode.PROVIDER_DISABLED)
        if not policy.credentials_present:
            return self._deny(policy, operation, DenialCode.CREDENTIALS_MISSING)
        if not policy.access_approved:
            return self._deny(policy, operation, DenialCode.ACCESS_NOT_APPROVED)
        if (
            context in {ExecutionContext.SCHEDULER, ExecutionContext.WORKER}
            and not policy.background_requests_allowed
        ):
            return self._deny(policy, operation, DenialCode.BACKGROUND_NOT_ALLOWED)

        click_gated_booking = (
            operation == ProviderOperation.BOOKING_ACTION and policy.booking_link_requires_click
        )
        if policy.user_action_required or click_gated_booking:
            grant_decision = self._authorize_grant(
                policy=policy,
                operation=operation,
                request_fingerprint=request_fingerprint,
                grant=user_action_grant,
            )
            if grant_decision is not None:
                return grant_decision

        return PolicyDecision(
            provider_id=policy.provider_id,
            operation=operation,
            allowed=True,
            code=DenialCode.ALLOWED,
            message="provider operation allowed by policy",
            merge_scope=policy.merge_scope,
            consumed_grant=(
                user_action_grant.consume(self._clock())
                if (policy.user_action_required or click_gated_booking)
                and user_action_grant is not None
                else None
            ),
        )

    def _authorize_grant(
        self,
        *,
        policy: ProviderPolicy,
        operation: ProviderOperation,
        request_fingerprint: str,
        grant: UserActionGrant | None,
    ) -> PolicyDecision | None:
        if grant is None:
            return self._deny(policy, operation, DenialCode.USER_ACTION_GRANT_REQUIRED)
        if grant.provider_id != policy.provider_id:
            return self._deny(policy, operation, DenialCode.USER_ACTION_GRANT_PROVIDER_MISMATCH)
        if grant.request_fingerprint != request_fingerprint:
            return self._deny(policy, operation, DenialCode.USER_ACTION_GRANT_FINGERPRINT_MISMATCH)
        if grant.consumed_at is not None:
            return self._deny(policy, operation, DenialCode.USER_ACTION_GRANT_CONSUMED)
        if grant.is_expired(self._clock()):
            return self._deny(policy, operation, DenialCode.USER_ACTION_GRANT_EXPIRED)
        return None

    @staticmethod
    def _deny(
        policy: ProviderPolicy,
        operation: ProviderOperation,
        code: DenialCode,
    ) -> PolicyDecision:
        return PolicyDecision(
            provider_id=policy.provider_id,
            operation=operation,
            allowed=False,
            code=code,
            message=code.value,
            merge_scope=policy.merge_scope,
        )
