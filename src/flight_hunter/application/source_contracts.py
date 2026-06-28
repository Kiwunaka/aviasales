from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from flight_hunter.application.provider_registry import ProviderRegistry, ProviderStatus
from flight_hunter.config import AppSettings


class ImplementationStage(StrEnum):
    IMPLEMENTED = "implemented"
    POLICY_SKELETON = "policy_skeleton"
    CONTRACT_ONLY = "contract_only"
    EXTERNAL_CLICKOUT = "external_clickout"


@dataclass(frozen=True, slots=True)
class SourceContract:
    source_id: str
    display_name: str
    stage: ImplementationStage
    adapter_module: str | None
    contract_file: str
    terms_url: str
    required_env: tuple[str, ...]
    operations: tuple[str, ...]
    invariants: tuple[str, ...]
    notes: str


@dataclass(frozen=True, slots=True)
class SourceReadiness:
    source_id: str
    display_name: str
    stage: ImplementationStage
    adapter_module: str | None
    contract_file: str
    terms_url: str
    required_env: tuple[str, ...]
    operations: tuple[str, ...]
    invariants: tuple[str, ...]
    notes: str
    enabled: bool
    credentials_present: bool
    access_approved: bool
    data_kind: str
    merge_scope: str
    background_requests_allowed: bool
    user_action_required: bool
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SourceContractCatalog:
    contracts: tuple[SourceContract, ...]
    provider_statuses: tuple[ProviderStatus, ...]

    @classmethod
    def default(
        cls,
        *,
        settings: AppSettings,
        registry: ProviderRegistry,
    ) -> SourceContractCatalog:
        return cls(
            contracts=_default_contracts(settings),
            provider_statuses=registry.statuses(),
        )

    def readiness(self) -> tuple[SourceReadiness, ...]:
        provider_statuses = {status.provider_id: status for status in self.provider_statuses}
        readiness: list[SourceReadiness] = []
        for contract in self.contracts:
            status = provider_statuses.get(contract.source_id)
            readiness.append(_readiness_for(contract, status))
        return tuple(readiness)


def _readiness_for(
    contract: SourceContract,
    status: ProviderStatus | None,
) -> SourceReadiness:
    blocked_reasons = list(status.blocked_reasons if status is not None else ())
    if contract.stage in {ImplementationStage.POLICY_SKELETON, ImplementationStage.CONTRACT_ONLY}:
        blocked_reasons.append("adapter_not_implemented")

    if status is None:
        return SourceReadiness(
            source_id=contract.source_id,
            display_name=contract.display_name,
            stage=contract.stage,
            adapter_module=contract.adapter_module,
            contract_file=contract.contract_file,
            terms_url=contract.terms_url,
            required_env=contract.required_env,
            operations=contract.operations,
            invariants=contract.invariants,
            notes=contract.notes,
            enabled=contract.stage == ImplementationStage.IMPLEMENTED,
            credentials_present=True,
            access_approved=True,
            data_kind="reference",
            merge_scope="not_applicable",
            background_requests_allowed=True,
            user_action_required=False,
            blocked_reasons=(),
        )

    return SourceReadiness(
        source_id=contract.source_id,
        display_name=contract.display_name,
        stage=contract.stage,
        adapter_module=contract.adapter_module,
        contract_file=contract.contract_file,
        terms_url=contract.terms_url,
        required_env=contract.required_env,
        operations=contract.operations,
        invariants=contract.invariants,
        notes=contract.notes,
        enabled=status.enabled,
        credentials_present=status.credentials_present,
        access_approved=status.access_approved,
        data_kind=status.data_kind.value,
        merge_scope=status.merge_scope.value,
        background_requests_allowed=status.background_requests_allowed,
        user_action_required=status.user_action_required,
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
    )


def _default_contracts(settings: AppSettings) -> tuple[SourceContract, ...]:
    return (
        SourceContract(
            source_id="fake",
            display_name="Deterministic demo provider",
            stage=ImplementationStage.IMPLEMENTED,
            adapter_module="flight_hunter.providers.fake",
            contract_file="docs/provider-contracts/demo-browser-observer.md",
            terms_url="https://flight-hunter.local/policies/fake-provider",
            required_env=(),
            operations=("search", "watch_scheduler_fixture"),
            invariants=("no_external_network", "deterministic_fixtures", "no_live_claims"),
            notes="Demo-only provider used to exercise product flows without external keys.",
        ),
        SourceContract(
            source_id="aviasales_data",
            display_name="Aviasales / Travelpayouts Data API",
            stage=ImplementationStage.IMPLEMENTED,
            adapter_module="flight_hunter.providers.aviasales_data.adapter",
            contract_file="docs/provider-contracts/aviasales-data.md",
            terms_url=(
                "https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API"
            ),
            required_env=(
                "AVIASALES_DATA_ENABLED",
                "TRAVELPAYOUTS_API_TOKEN",
                "TRAVELPAYOUTS_MARKER",
            ),
            operations=("cached_search", "safe_smoke_check"),
            invariants=(
                "cached_not_live",
                "server_side_token_only",
                f"internal_rate_limit_rpm={settings.aviasales_data_internal_rpm}",
                "no_raw_payload_persistence",
            ),
            notes=(
                "Typed HTTP client, query planner, mapper and smoke helper are implemented; "
                "broader Data API endpoints remain explicit follow-up work."
            ),
        ),
        SourceContract(
            source_id="aviasales_search",
            display_name="Aviasales Flight Search API",
            stage=ImplementationStage.POLICY_SKELETON,
            adapter_module=None,
            contract_file="docs/provider-contracts/aviasales-search.md",
            terms_url=(
                "https://support.travelpayouts.com/hc/en-us/articles/"
                "30565016140434-Aviasales-Flight-Search-API-real-time-and-multi-city-search"
            ),
            required_env=(
                "AVIASALES_SEARCH_ENABLED",
                "AVIASALES_SEARCH_ACCESS_APPROVED",
                "AVIASALES_SEARCH_CONFIRMED_MAU_50000",
                "AVIASALES_SEARCH_TOKEN",
                "AVIASALES_SEARCH_MARKER",
                "AVIASALES_SEARCH_REAL_HOST",
            ),
            operations=("user_action_live_search", "click_time_booking_action"),
            invariants=(
                "no_background_calls",
                "provider_isolated_results",
                "booking_link_click_gate",
                "no_booking_link_preload",
                "requires_real_user_ip",
            ),
            notes=(
                "Policy and gateway tests exist, but the adapter is intentionally not wired until "
                "approved access and current docs are re-verified."
            ),
        ),
        SourceContract(
            source_id="skyscanner_indicative",
            display_name="Skyscanner Indicative Prices",
            stage=ImplementationStage.CONTRACT_ONLY,
            adapter_module=None,
            contract_file="docs/PROVIDER_MATRIX.md",
            terms_url="https://developers.skyscanner.net/docs/flights-indicative-prices/overview",
            required_env=("SKYSCANNER_INDICATIVE_ENABLED", "SKYSCANNER_ACCESS_APPROVED"),
            operations=("indicative_flexible_discovery",),
            invariants=("disabled_until_partnership", "contract_flags_required"),
            notes=(
                "Not implemented; requires partnership approval and fixture-backed contract tests."
            ),
        ),
        SourceContract(
            source_id="skyscanner_live",
            display_name="Skyscanner Live Prices",
            stage=ImplementationStage.CONTRACT_ONLY,
            adapter_module=None,
            contract_file="docs/PROVIDER_MATRIX.md",
            terms_url="https://developers.skyscanner.net/docs/flights-live-prices/overview",
            required_env=("SKYSCANNER_LIVE_ENABLED", "SKYSCANNER_ACCESS_APPROVED"),
            operations=("user_generated_live_create_poll",),
            invariants=("no_background_calls", "user_action_required", "no_archived_sdk"),
            notes="Not implemented; must remain disabled until partnership approval.",
        ),
        SourceContract(
            source_id="duffel",
            display_name="Duffel Flights",
            stage=ImplementationStage.CONTRACT_ONLY,
            adapter_module=None,
            contract_file="docs/PROVIDER_MATRIX.md",
            terms_url="https://duffel.com/docs/api/v2/offer-requests",
            required_env=("DUFFEL_ENABLED", "DUFFEL_ACCESS_TOKEN", "DUFFEL_MODE"),
            operations=("offer_request", "offer_retrieve_before_purchase"),
            invariants=("test_live_mode_separation", "offer_expiry_required"),
            notes="Not implemented; future adapter must keep booking/payment feature-gated.",
        ),
        SourceContract(
            source_id="ourairports",
            display_name="OurAirports reference data",
            stage=ImplementationStage.IMPLEMENTED,
            adapter_module="flight_hunter.geo.ourairports_importer",
            contract_file="docs/PROVIDER_MATRIX.md",
            terms_url="https://ourairports.com/data/",
            required_env=("OURAIRPORTS_IMPORT_ENABLED",),
            operations=("airport_import", "airport_search", "nearby_airports"),
            invariants=("public_domain_csv", "provenance_visible", "no_airfare_savings_claim"),
            notes=(
                "SQLite-compatible importer and search repository exist; "
                "PostGIS remains future work."
            ),
        ),
    )
