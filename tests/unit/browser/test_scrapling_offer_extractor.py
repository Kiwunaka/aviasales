from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from flight_hunter.browser.html_extractor import DomSnapshot, ScraplingRuHtmlOfferExtractor
from flight_hunter.domain.money import Money
from flight_hunter.domain.offers import SearchIntent
from flight_hunter.domain.search_results import Confidence

pytest.importorskip("scrapling.parser")

NOW = datetime(2026, 6, 29, 14, 5, tzinfo=UTC)
FIXTURE = Path("tests/fixtures/browser/tutu/search_result_sanitized.html")


def test_scrapling_extractor_reads_sanitized_offer_cards() -> None:
    snapshot = DomSnapshot.from_html(
        source_id="tutu",
        final_url="https://www.tutu.ru/avia/search/",
        html=FIXTURE.read_text(encoding="utf-8"),
        captured_at=NOW,
    )
    extractor = ScraplingRuHtmlOfferExtractor(source_names={"tutu": "Туту"})

    result = extractor.extract(snapshot, _intent())

    assert result.confidence == Confidence.MEDIUM
    assert result.offers[0].total_price == Money(1_842_000, "RUB")
    assert result.offers[0].parser_version == extractor.parser_version


def _intent() -> SearchIntent:
    return SearchIntent(
        origin="MOW",
        destination="IST",
        departure_date="2026-09-10",
        return_date="2026-09-20",
        passengers=1,
        currency="RUB",
    )
