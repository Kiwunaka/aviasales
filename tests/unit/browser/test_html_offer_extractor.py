from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from flight_hunter.browser.html_extractor import DomSnapshot, GenericRuHtmlOfferExtractor
from flight_hunter.domain.money import Money
from flight_hunter.domain.offers import Freshness, SearchIntent
from flight_hunter.domain.search_results import Confidence

NOW = datetime(2026, 6, 29, 14, 0, tzinfo=UTC)
FIXTURE = Path("tests/fixtures/browser/tutu/search_result_sanitized.html")


def test_generic_ru_html_extractor_reads_sanitized_offer_card() -> None:
    snapshot = DomSnapshot.from_html(
        source_id="tutu",
        final_url="https://www.tutu.ru/avia/search/",
        html=FIXTURE.read_text(encoding="utf-8"),
        captured_at=NOW,
        title="Sanitized Tutu search result fixture",
    )
    extractor = GenericRuHtmlOfferExtractor(source_names={"tutu": "Туту"})

    result = extractor.extract(snapshot, _intent())

    assert result.confidence == Confidence.MEDIUM
    assert result.warnings == ()
    assert len(result.raw_price_candidates) == 1
    assert result.raw_price_candidates[0].accepted is True
    assert result.raw_price_candidates[0].amount == Money(1_842_000, "RUB")
    assert len(result.offers) == 1
    offer = result.offers[0]
    assert offer.source_id == "tutu"
    assert offer.source_name == "Туту"
    assert offer.provider_offer_id == "tutu-card-1"
    assert offer.origin == "MOW"
    assert offer.destination == "IST"
    assert offer.total_price == Money(1_842_000, "RUB")
    assert offer.observed_at == NOW
    assert offer.freshness == Freshness.BROWSER_OBSERVED
    assert offer.confidence == Confidence.MEDIUM
    assert offer.parser_version == extractor.parser_version
    assert offer.airline_name == "Turkish Airlines"
    assert offer.airline_iata == "TK"
    assert offer.stops == 1
    assert offer.seller_name == "Туту"


def test_generic_ru_html_extractor_does_not_accept_route_mismatch() -> None:
    snapshot = DomSnapshot.from_html(
        source_id="tutu",
        final_url="https://www.tutu.ru/avia/search/",
        html=FIXTURE.read_text(encoding="utf-8"),
        captured_at=NOW,
    )

    result = GenericRuHtmlOfferExtractor(source_names={"tutu": "Туту"}).extract(
        snapshot,
        SearchIntent(
            origin="WAW",
            destination="BCN",
            departure_date="2026-09-10",
            return_date="2026-09-20",
            passengers=1,
            currency="RUB",
        ),
    )

    assert result.offers == ()
    assert result.confidence == Confidence.LOW
    assert "route_mismatch" in result.warnings
    assert result.raw_price_candidates[0].accepted is False


def test_generic_ru_html_extractor_ignores_non_total_prices_without_offer_card() -> None:
    snapshot = DomSnapshot.from_html(
        source_id="tutu",
        final_url="https://www.tutu.ru/avia/search/",
        html="<html><body><span>Страховка 1 200 ₽</span></body></html>",
        captured_at=NOW,
    )

    result = GenericRuHtmlOfferExtractor(source_names={"tutu": "Туту"}).extract(
        snapshot,
        _intent(),
    )

    assert result.offers == ()
    assert result.raw_price_candidates == ()
    assert result.confidence == Confidence.NONE
    assert "no_offer_cards_found" in result.warnings


def _intent() -> SearchIntent:
    return SearchIntent(
        origin="MOW",
        destination="IST",
        departure_date="2026-09-10",
        return_date="2026-09-20",
        passengers=1,
        currency="RUB",
    )
