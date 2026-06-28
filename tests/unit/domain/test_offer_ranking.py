from __future__ import annotations

from datetime import UTC, datetime

from flight_hunter.domain.money import Money
from flight_hunter.domain.offers import FlightOffer, Freshness
from flight_hunter.domain.ranking import OfferRanker, offer_ranking_key

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)


def test_ranker_penalizes_stale_offer_even_when_it_is_slightly_cheaper() -> None:
    ranker = OfferRanker()
    stale_cheaper = _offer(
        provider_offer_id="stale-cheaper",
        amount_minor=49_000,
        freshness=Freshness.STALE,
    )
    cached_clear = _offer(
        provider_offer_id="cached-clear",
        amount_minor=50_000,
        freshness=Freshness.CACHED,
    )

    ranked = ranker.rank((stale_cheaper, cached_clear))

    assert [item.offer.provider_offer_id for item in ranked] == ["cached-clear", "stale-cheaper"]


def test_ranker_explains_live_confirmation_and_missing_baggage_data() -> None:
    ranker = OfferRanker()
    offer = _offer(
        provider_offer_id="cached-no-bags",
        amount_minor=50_000,
        freshness=Freshness.CACHED,
        requires_live_confirmation=True,
        baggage_summary=None,
    )

    ranked = ranker.rank((offer,))

    assert ranked[0].reasons == (
        "cached_price",
        "requires_live_confirmation",
        "baggage_unknown",
    )


def test_offer_ranking_key_includes_provider_and_offer_id() -> None:
    offer = _offer(provider_offer_id="offer-1", amount_minor=50_000)

    assert offer_ranking_key(offer) == "fake:offer-1"


def _offer(
    *,
    provider_offer_id: str,
    amount_minor: int,
    freshness: Freshness = Freshness.CACHED,
    requires_live_confirmation: bool = True,
    baggage_summary: str | None = "hand baggage included",
) -> FlightOffer:
    return FlightOffer(
        provider_id="fake",
        provider_offer_id=provider_offer_id,
        origin="WAW",
        destination="BCN",
        departure_date="2026-10-12",
        return_date="2026-10-19",
        total_price=Money(amount_minor, "PLN"),
        passengers=1,
        observed_at=NOW,
        freshness=freshness,
        requires_live_confirmation=requires_live_confirmation,
        baggage_summary=baggage_summary,
    )
