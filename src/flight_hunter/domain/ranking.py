from __future__ import annotations

from dataclasses import dataclass

from flight_hunter.domain.offers import FlightOffer, Freshness

_FRESHNESS_PENALTIES = {
    Freshness.LIVE: 0,
    Freshness.RECENT: 500,
    Freshness.CACHED: 1_000,
    Freshness.STALE: 20_000,
}


@dataclass(frozen=True, slots=True)
class RankedOffer:
    offer: FlightOffer
    score_minor_units: int
    reasons: tuple[str, ...]


class OfferRanker:
    def rank(self, offers: tuple[FlightOffer, ...]) -> tuple[RankedOffer, ...]:
        ranked = tuple(self._rank_offer(offer) for offer in offers)
        return tuple(
            sorted(
                ranked,
                key=lambda item: (
                    item.score_minor_units,
                    item.offer.total_price.minor_units,
                    item.offer.provider_id,
                    item.offer.provider_offer_id,
                ),
            )
        )

    def _rank_offer(self, offer: FlightOffer) -> RankedOffer:
        score = offer.total_price.minor_units + _FRESHNESS_PENALTIES[offer.freshness]
        reasons = [_freshness_reason(offer.freshness)]

        if offer.requires_live_confirmation:
            score += 2_500
            reasons.append("requires_live_confirmation")
        if offer.baggage_summary is None:
            score += 500
            reasons.append("baggage_unknown")

        return RankedOffer(offer=offer, score_minor_units=score, reasons=tuple(reasons))


def offer_ranking_key(offer: FlightOffer) -> str:
    return f"{offer.provider_id}:{offer.provider_offer_id}"


def _freshness_reason(freshness: Freshness) -> str:
    return {
        Freshness.LIVE: "live_price",
        Freshness.RECENT: "recent_price",
        Freshness.CACHED: "cached_price",
        Freshness.STALE: "stale_price",
    }[freshness]
