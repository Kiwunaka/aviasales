from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from flight_hunter.domain.offers import FlightOffer, SearchIntent
from flight_hunter.domain.policy import (
    DataKind,
    ExecutionContext,
    ProviderOperation,
    ProviderPolicy,
)
from flight_hunter.policy.guard import PolicyDecision, ProviderPolicyGuard
from flight_hunter.providers.aviasales_data.client import AviasalesDataClient
from flight_hunter.providers.aviasales_data.mapper import map_prices_for_dates_item
from flight_hunter.providers.aviasales_data.query_planner import AviasalesDataQueryPlanner


class AviasalesDataAdapter:
    def __init__(
        self,
        *,
        client: AviasalesDataClient,
        enabled: bool,
        credentials_present: bool,
        market: str = "pl",
        internal_rpm: int = 30,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._client = client
        self._clock = clock or (lambda: datetime.now(UTC))
        self.policy = _policy(
            terms_verified_at=self._clock(),
            enabled=enabled,
            credentials_present=credentials_present,
            internal_rpm=internal_rpm,
        )
        self._market = market
        self._guard = ProviderPolicyGuard(clock=self._clock)
        self._query_planner = AviasalesDataQueryPlanner()

    def authorize(
        self,
        *,
        operation: ProviderOperation,
        context: ExecutionContext,
        request_fingerprint: str,
    ) -> PolicyDecision:
        return self._guard.authorize(
            self.policy,
            operation=operation,
            context=context,
            request_fingerprint=request_fingerprint,
        )

    def search(
        self,
        intent: SearchIntent,
        *,
        request_fingerprint: str,
        context: ExecutionContext,
    ) -> tuple[FlightOffer, ...]:
        decision = self.authorize(
            operation=ProviderOperation.SEARCH,
            context=context,
            request_fingerprint=request_fingerprint,
        )
        if not decision.allowed:
            return ()

        plan = self._query_planner.plan(intent, market=self._market)
        if plan.query is None:
            return ()

        response = self._client.prices_for_dates(plan.query)
        return tuple(
            map_prices_for_dates_item(
                item,
                observed_at=response.received_at,
                passengers=intent.passengers,
            )
            for item in response.items
        )


def _policy(
    *,
    terms_verified_at: datetime,
    enabled: bool,
    credentials_present: bool,
    internal_rpm: int,
) -> ProviderPolicy:
    return ProviderPolicy(
        provider_id="aviasales_data",
        policy_version="2026-06-23",
        terms_url="https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API",
        terms_verified_at=terms_verified_at,
        enabled=enabled,
        credentials_present=credentials_present,
        access_approved=True,
        data_kind=DataKind.CACHED,
        background_requests_allowed=True,
        user_action_required=False,
        merge_with_other_sources_allowed=True,
        persist_raw_results_allowed=False,
        persist_normalized_results_allowed=True,
        booking_link_requires_click=True,
        preload_booking_links_allowed=False,
        server_side_only=True,
        real_user_ip_required=False,
        max_requests_per_minute=internal_rpm,
        max_requests_per_hour_per_user_ip=None,
        cache_ttl_seconds=21600,
        result_ttl_seconds=604800,
        max_concurrent_requests=2,
        supports_flexible_dates=True,
        supports_nearby_airports=False,
        supports_multi_city=False,
        supports_one_way=True,
        supports_round_trip=True,
        supports_baggage=False,
        supports_fare_rules=False,
        notes="Cached Travelpayouts/Aviasales Data API source.",
    )
