from __future__ import annotations

from datetime import UTC, datetime

from flight_hunter.application.search_planner import ProviderCandidate, SearchPlanner
from flight_hunter.domain.policy import DataKind, ExecutionContext, MergeScope, ProviderPolicy
from flight_hunter.policy.guard import DenialCode

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)


def provider_policy(provider_id: str, **overrides: object) -> ProviderPolicy:
    values: dict[str, object] = {
        "provider_id": provider_id,
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


def test_scheduler_plan_excludes_background_disallowed_provider() -> None:
    planner = SearchPlanner(clock=lambda: NOW)
    candidates = [
        ProviderCandidate(provider_policy("cached_ok")),
        ProviderCandidate(provider_policy("live_click_only", background_requests_allowed=False)),
    ]

    plan = planner.plan(
        candidates,
        context=ExecutionContext.SCHEDULER,
        request_fingerprint="sha256:watch",
    )

    assert [step.provider_id for step in plan.allowed] == ["cached_ok"]
    assert plan.denied["live_click_only"].code == DenialCode.BACKGROUND_NOT_ALLOWED


def test_provider_isolated_candidates_do_not_enter_mergeable_steps() -> None:
    planner = SearchPlanner(clock=lambda: NOW)
    isolated = provider_policy(
        "aviasales_search",
        data_kind=DataKind.LIVE,
        merge_with_other_sources_allowed=False,
        background_requests_allowed=False,
        user_action_required=True,
    )

    plan = planner.plan(
        [ProviderCandidate(provider_policy("fake")), ProviderCandidate(isolated)],
        context=ExecutionContext.WEB_USER_ACTION,
        request_fingerprint="sha256:search",
    )

    assert [step.provider_id for step in plan.mergeable] == ["fake"]
    assert [step.provider_id for step in plan.provider_isolated] == []
    assert plan.denied["aviasales_search"].code == DenialCode.USER_ACTION_GRANT_REQUIRED


def test_split_results_keeps_provider_isolated_out_of_ranking_pool() -> None:
    planner = SearchPlanner(clock=lambda: NOW)

    split = planner.split_results_by_merge_scope(
        {
            "fake": MergeScope.MERGEABLE,
            "aviasales_search": MergeScope.PROVIDER_ISOLATED,
            "private": MergeScope.PRIVATE_TRANSIENT,
        }
    )

    assert split.mergeable_provider_ids == ("fake",)
    assert split.provider_isolated_ids == ("aviasales_search",)
    assert split.private_transient_ids == ("private",)
