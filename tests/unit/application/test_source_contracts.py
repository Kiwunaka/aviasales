from __future__ import annotations

from datetime import UTC, datetime

from flight_hunter.application.provider_registry import ProviderRegistry
from flight_hunter.application.source_contracts import (
    ImplementationStage,
    SourceContractCatalog,
)
from flight_hunter.config import AppSettings

NOW = datetime(2026, 6, 29, 12, 0, tzinfo=UTC)


def _settings(*, aviasales_enabled: bool = False, token: str | None = None) -> AppSettings:
    return AppSettings(
        database_url="sqlite+aiosqlite:///./flight_hunter_dev.db",
        aviasales_data_enabled=aviasales_enabled,
        travelpayouts_api_token=token,
        aviasales_data_default_market="pl",
        aviasales_data_internal_rpm=30,
        telegram_enabled=False,
        telegram_webhook_secret=None,
    )


def test_source_contract_catalog_marks_aviasales_data_as_implemented_but_gated() -> None:
    settings = _settings()
    registry = ProviderRegistry.default(clock=lambda: NOW, settings=settings)
    catalog = SourceContractCatalog.default(settings=settings, registry=registry)

    sources = {source.source_id: source for source in catalog.readiness()}

    aviasales_data = sources["aviasales_data"]
    assert aviasales_data.stage == ImplementationStage.IMPLEMENTED
    assert aviasales_data.adapter_module == "flight_hunter.providers.aviasales_data.adapter"
    assert aviasales_data.data_kind == "cached"
    assert aviasales_data.background_requests_allowed is True
    assert aviasales_data.merge_scope == "mergeable"
    assert aviasales_data.enabled is False
    assert aviasales_data.credentials_present is False
    assert "credentials_missing" in aviasales_data.blocked_reasons
    assert "AVIASALES_DATA_ENABLED" in aviasales_data.required_env
    assert "TRAVELPAYOUTS_API_TOKEN" in aviasales_data.required_env


def test_source_contract_catalog_reflects_enabled_credentials_without_leaking_values() -> None:
    settings = _settings(aviasales_enabled=True, token="secret-value")
    registry = ProviderRegistry.default(clock=lambda: NOW, settings=settings)
    catalog = SourceContractCatalog.default(settings=settings, registry=registry)

    aviasales_data = {source.source_id: source for source in catalog.readiness()}["aviasales_data"]

    assert aviasales_data.enabled is True
    assert aviasales_data.credentials_present is True
    assert aviasales_data.blocked_reasons == ()
    assert "secret-value" not in str(aviasales_data)


def test_source_contract_catalog_keeps_aviasales_search_isolated_and_user_action_only() -> None:
    registry = ProviderRegistry.default(clock=lambda: NOW, settings=_settings())
    catalog = SourceContractCatalog.default(settings=_settings(), registry=registry)

    aviasales_search = {source.source_id: source for source in catalog.readiness()}[
        "aviasales_search"
    ]

    assert aviasales_search.stage == ImplementationStage.POLICY_SKELETON
    assert aviasales_search.data_kind == "live"
    assert aviasales_search.merge_scope == "provider_isolated"
    assert aviasales_search.background_requests_allowed is False
    assert aviasales_search.user_action_required is True
    assert aviasales_search.enabled is False
    assert "access_not_approved" in aviasales_search.blocked_reasons
    assert "adapter_not_implemented" in aviasales_search.blocked_reasons
    assert "booking_link_click_gate" in aviasales_search.invariants


def test_every_policy_provider_has_a_source_contract() -> None:
    registry = ProviderRegistry.default(clock=lambda: NOW, settings=_settings())
    catalog = SourceContractCatalog.default(settings=_settings(), registry=registry)

    policy_ids = {status.provider_id for status in registry.statuses()}
    contract_ids = {source.source_id for source in catalog.readiness()}

    assert policy_ids <= contract_ids


def test_unimplemented_live_and_bookable_sources_remain_disabled() -> None:
    registry = ProviderRegistry.default(clock=lambda: NOW, settings=_settings())
    catalog = SourceContractCatalog.default(settings=_settings(), registry=registry)

    sources = {source.source_id: source for source in catalog.readiness()}

    for source_id in ("skyscanner_live", "duffel"):
        source = sources[source_id]
        assert source.stage == ImplementationStage.CONTRACT_ONLY
        assert source.enabled is False
        assert source.credentials_present is False
        assert source.access_approved is False
        assert "adapter_not_implemented" in source.blocked_reasons
