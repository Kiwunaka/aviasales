from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from flight_hunter.domain.policy import (
    ExecutionContext,
    MergeScope,
    ProviderOperation,
    ProviderPolicy,
    UserActionGrant,
)
from flight_hunter.policy.guard import PolicyDecision, ProviderPolicyGuard


@dataclass(frozen=True, slots=True)
class ProviderCandidate:
    policy: ProviderPolicy
    user_action_grant: UserActionGrant | None = None


@dataclass(frozen=True, slots=True)
class ProviderPlanStep:
    provider_id: str
    policy_snapshot: ProviderPolicy
    merge_scope: MergeScope
    consumed_grant: UserActionGrant | None


@dataclass(frozen=True, slots=True)
class SearchPlan:
    allowed: tuple[ProviderPlanStep, ...]
    denied: Mapping[str, PolicyDecision]

    @property
    def mergeable(self) -> tuple[ProviderPlanStep, ...]:
        return tuple(step for step in self.allowed if step.merge_scope == MergeScope.MERGEABLE)

    @property
    def provider_isolated(self) -> tuple[ProviderPlanStep, ...]:
        return tuple(
            step for step in self.allowed if step.merge_scope == MergeScope.PROVIDER_ISOLATED
        )


@dataclass(frozen=True, slots=True)
class ResultScopeSplit:
    mergeable_provider_ids: tuple[str, ...]
    provider_isolated_ids: tuple[str, ...]
    private_transient_ids: tuple[str, ...]


class SearchPlanner:
    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._guard = ProviderPolicyGuard(clock=clock or (lambda: datetime.now(UTC)))

    def plan(
        self,
        candidates: list[ProviderCandidate],
        *,
        context: ExecutionContext,
        request_fingerprint: str,
    ) -> SearchPlan:
        allowed: list[ProviderPlanStep] = []
        denied: dict[str, PolicyDecision] = {}

        for candidate in candidates:
            decision = self._guard.authorize(
                candidate.policy,
                operation=ProviderOperation.SEARCH,
                context=context,
                request_fingerprint=request_fingerprint,
                user_action_grant=candidate.user_action_grant,
            )
            if decision.allowed:
                allowed.append(
                    ProviderPlanStep(
                        provider_id=candidate.policy.provider_id,
                        policy_snapshot=candidate.policy,
                        merge_scope=decision.merge_scope,
                        consumed_grant=decision.consumed_grant,
                    )
                )
            else:
                denied[candidate.policy.provider_id] = decision

        return SearchPlan(allowed=tuple(allowed), denied=denied)

    @staticmethod
    def split_results_by_merge_scope(scopes: Mapping[str, MergeScope]) -> ResultScopeSplit:
        mergeable: list[str] = []
        isolated: list[str] = []
        private: list[str] = []

        for provider_id, scope in scopes.items():
            if scope == MergeScope.MERGEABLE:
                mergeable.append(provider_id)
            elif scope == MergeScope.PROVIDER_ISOLATED:
                isolated.append(provider_id)
            elif scope == MergeScope.PRIVATE_TRANSIENT:
                private.append(provider_id)

        return ResultScopeSplit(
            mergeable_provider_ids=tuple(mergeable),
            provider_isolated_ids=tuple(isolated),
            private_transient_ids=tuple(private),
        )
