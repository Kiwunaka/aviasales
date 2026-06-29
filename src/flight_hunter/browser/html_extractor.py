from __future__ import annotations

import hashlib
import importlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from uuid import NAMESPACE_URL, uuid5

from flight_hunter.domain.money import Money
from flight_hunter.domain.offers import Freshness, SearchIntent
from flight_hunter.domain.policy import require_aware_datetime
from flight_hunter.domain.search_results import BrowserObservedOffer, Confidence

PRICE_RE = re.compile(
    "(?<!\\d)(\\d[\\d\\s\u00a0]{2,8})\\s*(\u20bd|\u0440\u0443\u0431\\.?|RUB)(?!\\w)",
    re.IGNORECASE,
)
MIN_AIRFARE_RUB = 500
MAX_AIRFARE_RUB = 2_000_000


@dataclass(frozen=True, slots=True)
class DomSnapshot:
    source_id: str
    final_url: str
    title: str | None
    html: str
    text: str
    captured_at: datetime
    visible_text_hash: str
    html_hash: str
    screenshot_path: str | None = None

    @classmethod
    def from_html(
        cls,
        *,
        source_id: str,
        final_url: str,
        html: str,
        captured_at: datetime,
        title: str | None = None,
        screenshot_path: str | None = None,
    ) -> DomSnapshot:
        text = _visible_text(html)
        return cls(
            source_id=source_id,
            final_url=final_url,
            title=title,
            html=html,
            text=text,
            captured_at=captured_at,
            visible_text_hash=_sha256(text),
            html_hash=_sha256(html),
            screenshot_path=screenshot_path,
        )

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id is required")
        if not self.final_url.startswith(("https://", "http://")):
            raise ValueError("final_url must be http(s)")
        if not self.html:
            raise ValueError("html is required")
        require_aware_datetime(self.captured_at, "captured_at")


@dataclass(frozen=True, slots=True)
class PriceCandidate:
    raw_text: str
    amount: Money
    context: str
    accepted: bool
    rejection_reason: str | None = None


@dataclass(frozen=True, slots=True)
class BrowserExtractionResult:
    offers: tuple[BrowserObservedOffer, ...]
    warnings: tuple[str, ...]
    confidence: Confidence
    raw_price_candidates: tuple[PriceCandidate, ...]


class GenericRuHtmlOfferExtractor:
    parser_id = "generic_ru_html_fixture"
    parser_version = "generic_ru_html_fixture:2026-06-29"
    supported_source_ids = ("tutu", "yandex_travel", "onetwotrip", "demo_browser")

    def __init__(self, *, source_names: Mapping[str, str] | None = None) -> None:
        self._source_names = dict(source_names or {})

    def extract(self, snapshot: DomSnapshot, intent: SearchIntent) -> BrowserExtractionResult:
        parser = _OfferHtmlParser()
        parser.feed(snapshot.html)
        cards = tuple(parser.cards)
        if not cards:
            return BrowserExtractionResult(
                offers=(),
                warnings=("no_offer_cards_found",),
                confidence=Confidence.NONE,
                raw_price_candidates=(),
            )

        offers: list[BrowserObservedOffer] = []
        candidates: list[PriceCandidate] = []
        warnings: set[str] = set()
        for card in cards:
            price = _first_price(card.price_text)
            if price is None:
                warnings.add("card_missing_price")
                continue
            route_matches = _matches_route(card, intent)
            date_matches = _matches_dates(card, intent)
            accepted = route_matches and date_matches
            if not route_matches:
                warnings.add("route_mismatch")
            if not date_matches:
                warnings.add("date_mismatch")
            candidates.append(
                PriceCandidate(
                    raw_text=price.raw_text,
                    amount=price.amount,
                    context=card.text,
                    accepted=accepted,
                    rejection_reason=None if accepted else "intent_mismatch",
                )
            )
            if not accepted:
                continue
            offers.append(
                self._offer_from_card(card, snapshot=snapshot, intent=intent, price=price)
            )

        if not offers:
            warnings.add("parser_no_offers")
        confidence = Confidence.MEDIUM if offers else Confidence.LOW
        return BrowserExtractionResult(
            offers=tuple(offers),
            warnings=tuple(sorted(warnings)),
            confidence=confidence,
            raw_price_candidates=tuple(candidates),
        )

    def _offer_from_card(
        self,
        card: _OfferCard,
        *,
        snapshot: DomSnapshot,
        intent: SearchIntent,
        price: _ParsedPrice,
    ) -> BrowserObservedOffer:
        parser_warnings: list[str] = []
        if not card.baggage_summary:
            parser_warnings.append("baggage_unknown")
        observation_seed = "|".join(
            (
                snapshot.source_id,
                snapshot.final_url,
                card.source_offer_id or card.text,
                str(price.amount.minor_units),
                snapshot.html_hash,
            )
        )
        return BrowserObservedOffer(
            observation_id=uuid5(NAMESPACE_URL, observation_seed),
            source_id=snapshot.source_id,
            source_name=self._source_names.get(snapshot.source_id, snapshot.source_id),
            provider_offer_id=card.source_offer_id or f"{snapshot.source_id}:{snapshot.html_hash}",
            origin=card.origin or intent.origin,
            destination=card.destination or intent.destination,
            departure_date=card.departure_date or intent.departure_date,
            return_date=card.return_date or intent.return_date,
            total_price=price.amount,
            passengers=intent.passengers,
            observed_at=snapshot.captured_at,
            final_url=snapshot.final_url,
            display_url=_display_url(snapshot.final_url),
            freshness=Freshness.BROWSER_OBSERVED,
            confidence=Confidence.MEDIUM,
            parser_version=self.parser_version,
            parser_warnings=tuple(parser_warnings),
            airline_name=card.airline_name,
            airline_iata=card.airline_iata,
            stops=card.stops,
            baggage_summary=card.baggage_summary,
            seller_name=card.seller_name,
        )


class ScraplingRuHtmlOfferExtractor:
    parser_id = "scrapling_ru_html_fixture"
    parser_version = "scrapling_ru_html_fixture:2026-06-29"
    supported_source_ids = GenericRuHtmlOfferExtractor.supported_source_ids

    def __init__(self, *, source_names: Mapping[str, str] | None = None) -> None:
        self._generic = GenericRuHtmlOfferExtractor(source_names=source_names)

    def extract(self, snapshot: DomSnapshot, intent: SearchIntent) -> BrowserExtractionResult:
        parser_module = importlib.import_module("scrapling.parser")
        adaptor = parser_module.Adaptor(snapshot.html, url=snapshot.final_url)
        cards = adaptor.css("[data-flight-offer]")
        if not cards:
            return BrowserExtractionResult(
                offers=(),
                warnings=("no_offer_cards_found",),
                confidence=Confidence.NONE,
                raw_price_candidates=(),
            )
        result = self._generic.extract(snapshot, intent)
        offers = tuple(
            _replace_parser_version(offer, self.parser_version) for offer in result.offers
        )
        return BrowserExtractionResult(
            offers=offers,
            warnings=result.warnings,
            confidence=result.confidence,
            raw_price_candidates=result.raw_price_candidates,
        )


@dataclass(frozen=True, slots=True)
class _OfferCard:
    source_offer_id: str | None
    origin: str | None
    destination: str | None
    departure_date: str | None
    return_date: str | None
    airline_name: str | None
    airline_iata: str | None
    stops: int | None
    baggage_summary: str | None
    seller_name: str | None
    price_text: str
    text: str


@dataclass(frozen=True, slots=True)
class _ParsedPrice:
    raw_text: str
    amount: Money


class _CardBuilder:
    def __init__(self, attrs: Mapping[str, str]) -> None:
        self.source_offer_id = attrs.get("data-source-offer-id")
        self.origin = _upper_or_none(attrs.get("data-origin"))
        self.destination = _upper_or_none(attrs.get("data-destination"))
        self.departure_date = attrs.get("data-departure-date")
        self.return_date = attrs.get("data-return-date")
        self.airline_name = attrs.get("data-airline-name")
        self.airline_iata = _upper_or_none(attrs.get("data-airline-iata"))
        self.stops = _int_or_none(attrs.get("data-stops"))
        self.baggage_summary = attrs.get("data-baggage-summary")
        self.seller_name = attrs.get("data-seller-name")
        self.price_parts: list[str] = []
        self.text_parts: list[str] = []

    def build(self) -> _OfferCard:
        return _OfferCard(
            source_offer_id=self.source_offer_id,
            origin=self.origin,
            destination=self.destination,
            departure_date=self.departure_date,
            return_date=self.return_date,
            airline_name=self.airline_name,
            airline_iata=self.airline_iata,
            stops=self.stops,
            baggage_summary=self.baggage_summary,
            seller_name=self.seller_name,
            price_text=" ".join(self.price_parts),
            text=_normalize_text(" ".join(self.text_parts)),
        )


class _OfferHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: list[_OfferCard] = []
        self._current: _CardBuilder | None = None
        self._card_depth = 0
        self._price_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        starts_card = "data-flight-offer" in attr_map
        if starts_card and self._current is None:
            self._current = _CardBuilder(attr_map)
            self._card_depth = 1
        elif self._current is not None:
            self._card_depth += 1

        if self._current is not None and "data-price" in attr_map:
            self._price_depth = 1
        elif self._price_depth > 0:
            self._price_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self._price_depth > 0:
            self._price_depth -= 1
        if self._current is None:
            return
        self._card_depth -= 1
        if self._card_depth == 0:
            self.cards.append(self._current.build())
            self._current = None

    def handle_data(self, data: str) -> None:
        if self._current is None:
            return
        stripped = data.strip()
        if not stripped:
            return
        self._current.text_parts.append(stripped)
        if self._price_depth > 0:
            self._current.price_parts.append(stripped)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if stripped:
            self.parts.append(stripped)


def _visible_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return _normalize_text(" ".join(parser.parts))


def _first_price(value: str) -> _ParsedPrice | None:
    for match in PRICE_RE.finditer(value):
        raw_number = match.group(1)
        rub = int(re.sub(r"[\s\u00a0]", "", raw_number))
        if rub < MIN_AIRFARE_RUB or rub > MAX_AIRFARE_RUB:
            continue
        return _ParsedPrice(
            raw_text=match.group(0),
            amount=Money(rub * 100, "RUB"),
        )
    return None


def _matches_route(card: _OfferCard, intent: SearchIntent) -> bool:
    return (card.origin is None or card.origin == intent.origin) and (
        card.destination is None or card.destination == intent.destination
    )


def _matches_dates(card: _OfferCard, intent: SearchIntent) -> bool:
    return (card.departure_date is None or card.departure_date == intent.departure_date) and (
        card.return_date is None or card.return_date == intent.return_date
    )


def _display_url(url: str) -> str:
    return url.removeprefix("https://").removeprefix("http://").split("/", 1)[0]


def _upper_or_none(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return value.strip().upper()


def _int_or_none(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _sha256(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _replace_parser_version(
    offer: BrowserObservedOffer,
    parser_version: str,
) -> BrowserObservedOffer:
    return BrowserObservedOffer(
        observation_id=offer.observation_id,
        source_id=offer.source_id,
        source_name=offer.source_name,
        provider_offer_id=offer.provider_offer_id,
        origin=offer.origin,
        destination=offer.destination,
        departure_date=offer.departure_date,
        return_date=offer.return_date,
        total_price=offer.total_price,
        passengers=offer.passengers,
        observed_at=offer.observed_at,
        final_url=offer.final_url,
        display_url=offer.display_url,
        freshness=offer.freshness,
        confidence=offer.confidence,
        parser_version=parser_version,
        parser_warnings=offer.parser_warnings,
        airline_name=offer.airline_name,
        airline_iata=offer.airline_iata,
        flight_number=offer.flight_number,
        departure_time_local=offer.departure_time_local,
        arrival_time_local=offer.arrival_time_local,
        duration_minutes=offer.duration_minutes,
        stops=offer.stops,
        baggage_summary=offer.baggage_summary,
        seller_name=offer.seller_name,
        requires_external_confirmation=offer.requires_external_confirmation,
    )
