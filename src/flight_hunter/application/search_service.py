from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from flight_hunter.application.provider_registry import ProviderRegistry
from flight_hunter.application.search_planner import SearchPlanner
from flight_hunter.domain.offers import FlightOffer, SearchIntent
from flight_hunter.domain.policy import ExecutionContext, MergeScope
from flight_hunter.domain.ranking import OfferRanker, offer_ranking_key
from flight_hunter.providers.fake import FakeFlightProvider


class SearchProvider(Protocol):
    def search(
        self,
        intent: SearchIntent,
        *,
        request_fingerprint: str,
        context: ExecutionContext,
    ) -> tuple[FlightOffer, ...]: ...


@dataclass(frozen=True, slots=True)
class SearchRequest:
    origin: str
    destination: str
    departure_date: str
    return_date: str | None
    passengers: int
    currency: str
    provider_ids: tuple[str, ...] | None
    adults: int | None = None
    children: int = 0
    infants: int = 0
    trip_type: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderDenial:
    provider_id: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class SearchResult:
    search_id: str
    mergeable_offers: tuple[FlightOffer, ...]
    provider_isolated_offers: tuple[FlightOffer, ...]
    ranking_reasons: dict[str, tuple[str, ...]]
    denied_providers: dict[str, ProviderDenial]


class DemoSearchService:
    def __init__(
        self,
        *,
        registry: ProviderRegistry,
        clock: Callable[[], datetime] | None = None,
        providers: Mapping[str, SearchProvider] | None = None,
    ) -> None:
        self._registry = registry
        self._clock = clock or (lambda: datetime.now(UTC))
        self._planner = SearchPlanner(clock=self._clock)
        self._ranker = OfferRanker()
        self._fake_provider = FakeFlightProvider(clock=self._clock)
        self._providers: dict[str, SearchProvider] = {"fake": self._fake_provider}
        if providers is not None:
            self._providers.update(providers)

    def search(self, request: SearchRequest) -> SearchResult:
        intent = SearchIntent(
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            return_date=request.return_date,
            passengers=request.passengers,
            currency=request.currency,
            adults=request.adults,
            children=request.children,
            infants=request.infants,
            trip_type=request.trip_type,
        )
        request_fingerprint = self._fingerprint(request)
        plan = self._planner.plan(
            list(self._registry.planning_candidates(request.provider_ids)),
            context=ExecutionContext.WEB_USER_ACTION,
            request_fingerprint=request_fingerprint,
        )
        denied = {
            provider_id: ProviderDenial(
                provider_id=provider_id,
                code=decision.code.value,
                message=decision.message,
            )
            for provider_id, decision in plan.denied.items()
        }

        mergeable: list[FlightOffer] = []
        provider_isolated: list[FlightOffer] = []
        for step in plan.allowed:
            provider = self._providers.get(step.provider_id)
            if provider is None:
                continue
            offers = provider.search(
                intent,
                request_fingerprint=request_fingerprint,
                context=ExecutionContext.WEB_USER_ACTION,
            )
            if step.merge_scope == MergeScope.MERGEABLE:
                mergeable.extend(offers)
            elif step.merge_scope == MergeScope.PROVIDER_ISOLATED:
                provider_isolated.extend(offers)

        ranked_mergeable = self._ranker.rank(tuple(mergeable))
        return SearchResult(
            search_id=request_fingerprint,
            mergeable_offers=tuple(item.offer for item in ranked_mergeable),
            provider_isolated_offers=tuple(provider_isolated),
            ranking_reasons={
                offer_ranking_key(item.offer): item.reasons for item in ranked_mergeable
            },
            denied_providers=denied,
        )

    @staticmethod
    def _fingerprint(request: SearchRequest) -> str:
        provider_part = ",".join(request.provider_ids or ())
        raw = "|".join(
            (
                request.origin.upper(),
                request.destination.upper(),
                request.departure_date,
                request.return_date or "",
                str(request.passengers),
                str(request.adults) if request.adults is not None else "",
                str(request.children),
                str(request.infants),
                request.trip_type or "",
                request.currency.upper(),
                provider_part,
            )
        )
        return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()
