from __future__ import annotations

from collections.abc import Sequence
from urllib.parse import urlparse

from flight_hunter.domain.offers import SearchIntent, TripType
from flight_hunter.domain.search_results import ExternalSearchLink
from flight_hunter.providers.ru_clickout.source_specs import RuAggregatorSpec


class RuClickoutLinkBuilder:
    def __init__(self, specs: Sequence[RuAggregatorSpec]) -> None:
        self._specs = tuple(specs)

    def build_all(
        self,
        intent: SearchIntent,
        *,
        enabled_source_ids: Sequence[str] | None = None,
    ) -> tuple[ExternalSearchLink, ...]:
        enabled = set(enabled_source_ids) if enabled_source_ids is not None else None
        links: list[ExternalSearchLink] = []
        for spec in self._specs:
            if enabled is not None and spec.source_id not in enabled:
                continue
            if not self.can_build(spec, intent):
                continue
            links.append(self.build(spec, intent))
        return tuple(links)

    def can_build(self, spec: RuAggregatorSpec, intent: SearchIntent) -> bool:
        if intent.trip_type == TripType.ONE_WAY and not spec.supports_one_way:
            return False
        return not (intent.trip_type == TripType.ROUND_TRIP and not spec.supports_round_trip)

    def build(self, spec: RuAggregatorSpec, intent: SearchIntent) -> ExternalSearchLink:
        warnings = _warnings(spec, intent)
        notes = _notes_ru(spec, warnings=warnings)
        url = _safe_base_url(spec)
        return ExternalSearchLink(
            source_id=spec.source_id,
            source_name=spec.display_name,
            url=url,
            origin=intent.origin,
            destination=intent.destination,
            departure_date=intent.departure_date,
            return_date=intent.return_date,
            passengers=intent.passengers,
            adults=intent.passenger_mix.adults,
            children=intent.passenger_mix.children,
            infants=intent.passenger_mix.infants,
            currency=intent.currency if spec.supports_currency_param else spec.default_currency,
            source_type=spec.source_type,
            purchase_flow="external_clickout" if spec.source_type != "deal" else "manual_check",
            price_known=False,
            requires_external_confirmation=True,
            notes_ru=notes,
            warnings=warnings,
        )


def _safe_base_url(spec: RuAggregatorSpec) -> str:
    parsed = urlparse(spec.base_url)
    host = parsed.netloc.lower()
    if parsed.scheme != "https" or host not in spec.allowed_hosts:
        raise ValueError(f"unsafe base_url for {spec.source_id}")
    return spec.base_url


def _warnings(spec: RuAggregatorSpec, intent: SearchIntent) -> tuple[str, ...]:
    warnings: list[str] = ["external_link_price_unknown"]
    mix = intent.passenger_mix
    if not spec.supports_passenger_mix and intent.passengers != 1:
        warnings.append("passenger_mix_not_prefilled")
    if mix.children > 0 and not spec.supports_children:
        warnings.append("children_not_prefilled")
    if mix.infants > 0 and not spec.supports_infants:
        warnings.append("infants_not_prefilled")
    if intent.currency != spec.default_currency and not spec.supports_currency_param:
        warnings.append("currency_not_prefilled")
    return tuple(warnings)


def _notes_ru(spec: RuAggregatorSpec, *, warnings: tuple[str, ...]) -> str:
    base = (
        f"Откройте {spec.display_name} и заполните маршрут, даты и пассажиров вручную. "
        "Flight Hunter не считает эту ссылку найденным билетом или live-ценой."
    )
    if "passenger_mix_not_prefilled" in warnings:
        return base + " Состав пассажиров нужно проверить на внешнем сайте."
    return base
