from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from flight_hunter.domain.money import Money
from flight_hunter.domain.offers import Freshness
from flight_hunter.domain.search_results import (
    BrowserObservedOffer,
    Confidence,
    DealCandidate,
    ExternalSearchLink,
    FreshnessSummary,
    ResultKind,
    SearchBundle,
)

NOW = datetime(2026, 6, 29, 12, 0, tzinfo=UTC)


def test_external_search_link_represents_unknown_price_clickout() -> None:
    link = ExternalSearchLink(
        source_id="tutu",
        source_name="Туту",
        url="https://www.tutu.ru/",
        origin="mow",
        destination="ist",
        departure_date="2026-09-10",
        return_date="2026-09-20",
        passengers=2,
        adults=2,
        children=0,
        infants=0,
        currency="rub",
        source_type="aggregator",
        purchase_flow="external_clickout",
        notes_ru="Откройте внешний сайт и проверьте цену.",
    )

    assert link.kind == ResultKind.EXTERNAL_SEARCH_LINK
    assert link.origin == "MOW"
    assert link.destination == "IST"
    assert link.currency == "RUB"
    assert link.price_known is False
    assert link.requires_external_confirmation is True


def test_external_search_link_validates_passenger_mix_and_purchase_flow() -> None:
    with pytest.raises(ValueError, match="passengers must match passenger mix total"):
        ExternalSearchLink(
            source_id="bad",
            source_name="Bad",
            url="https://example.test",
            origin="WAW",
            destination="BCN",
            departure_date="2026-10-12",
            return_date=None,
            passengers=3,
            adults=1,
            children=1,
            infants=0,
            currency="RUB",
            source_type="aggregator",
            purchase_flow="external_clickout",
        )

    with pytest.raises(ValueError, match="unsupported purchase_flow"):
        ExternalSearchLink(
            source_id="bad",
            source_name="Bad",
            url="https://example.test",
            origin="WAW",
            destination="BCN",
            departure_date="2026-10-12",
            return_date=None,
            passengers=1,
            adults=1,
            children=0,
            infants=0,
            currency="RUB",
            source_type="aggregator",
            purchase_flow="buy_inside_app",
        )


def test_browser_observed_offer_requires_aware_observed_at_and_keeps_parser_context() -> None:
    offer = BrowserObservedOffer(
        observation_id=UUID("00000000-0000-0000-0000-000000000001"),
        source_id="tutu",
        source_name="Туту",
        provider_offer_id="dom-card-1",
        origin="MOW",
        destination="IST",
        departure_date="2026-09-10",
        return_date="2026-09-20",
        total_price=Money(1842000, "RUB"),
        passengers=1,
        observed_at=NOW,
        final_url="https://www.tutu.ru/",
        display_url="www.tutu.ru",
        freshness=Freshness.BROWSER_OBSERVED,
        confidence=Confidence.MEDIUM,
        parser_version="tutu-fixture-v1",
        parser_warnings=("baggage_unknown",),
        seller_name="Туту",
    )

    assert offer.kind == ResultKind.BROWSER_OBSERVATION
    assert offer.total_price == Money(1842000, "RUB")
    assert offer.requires_external_confirmation is True
    assert offer.parser_warnings == ("baggage_unknown",)

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        BrowserObservedOffer(
            observation_id=UUID("00000000-0000-0000-0000-000000000002"),
            source_id="tutu",
            source_name="Туту",
            provider_offer_id="dom-card-2",
            origin="MOW",
            destination="IST",
            departure_date=None,
            return_date=None,
            total_price=None,
            passengers=1,
            observed_at=datetime(2026, 6, 29, 12, 0),
            final_url="https://www.tutu.ru/",
            display_url="www.tutu.ru",
            freshness=Freshness.BROWSER_OBSERVED,
            confidence=Confidence.NONE,
            parser_version="tutu-fixture-v1",
            parser_warnings=("parser_no_price",),
        )


def test_search_bundle_summarizes_confirmation_need_without_hiding_empty_sections() -> None:
    link = ExternalSearchLink(
        source_id="aviasales_clickout",
        source_name="Aviasales",
        url="https://www.aviasales.ru/",
        origin="WAW",
        destination="BCN",
        departure_date="2026-10-12",
        return_date="2026-10-19",
        passengers=2,
        adults=2,
        children=0,
        infants=0,
        currency="RUB",
        source_type="aggregator",
        purchase_flow="external_clickout",
    )
    bundle = SearchBundle(
        search_id="sha256:test",
        priced_offers=(),
        provider_isolated_offers=(),
        browser_observed_offers=(),
        external_links=(link,),
        deal_candidates=(
            DealCandidate(
                source_id="manual_deal",
                url="https://example.test/deal",
                title="Possible fare sale",
                summary_ru="Требует ручной проверки.",
                extracted_price=None,
                extracted_origin="WAW",
                extracted_destination="BCN",
                extracted_date_window="октябрь",
                confidence=Confidence.LOW,
                discovered_at=NOW,
            ),
        ),
        denied_sources={},
        warnings=("external_links_are_not_prices",),
        freshness_summary=FreshnessSummary(
            best_price_source=None,
            freshest_observation_at=None,
            needs_external_confirmation=True,
        ),
    )

    assert bundle.external_links == (link,)
    assert bundle.freshness_summary.needs_external_confirmation is True
    assert bundle.deal_candidates[0].requires_manual_verification is True
