from __future__ import annotations

from datetime import UTC, datetime

from flight_hunter.application.provider_registry import ProviderRegistry
from flight_hunter.domain.policy import DataKind, MergeScope

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)


def test_default_registry_exposes_policy_derived_provider_statuses() -> None:
    registry = ProviderRegistry.default(clock=lambda: NOW)

    providers = {status.provider_id: status for status in registry.statuses()}

    assert providers["fake"].enabled
    assert providers["fake"].data_kind == DataKind.CACHED
    assert providers["fake"].merge_scope == MergeScope.MERGEABLE
    assert providers["aviasales_search"].merge_scope == MergeScope.PROVIDER_ISOLATED
    assert "credentials_missing" in providers["aviasales_search"].blocked_reasons
    assert "access_not_approved" in providers["aviasales_search"].blocked_reasons
    assert "provider_disabled" in providers["aviasales_search"].blocked_reasons


def test_default_registry_search_candidates_include_enabled_demo_provider_only() -> None:
    registry = ProviderRegistry.default(clock=lambda: NOW)

    candidates = registry.search_candidates(provider_ids=None)

    assert [candidate.policy.provider_id for candidate in candidates] == ["fake"]
