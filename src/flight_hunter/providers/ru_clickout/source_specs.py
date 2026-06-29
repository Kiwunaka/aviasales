from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

LinkStrategy = Literal["known_template", "search_page", "query_search", "manual"]


@dataclass(frozen=True, slots=True)
class RuAggregatorSpec:
    source_id: str
    display_name: str
    base_url: str
    allowed_hosts: tuple[str, ...]
    supports_one_way: bool
    supports_round_trip: bool
    supports_multi_city: bool
    supports_passenger_mix: bool
    supports_children: bool
    supports_infants: bool
    supports_baggage_query: bool
    supports_currency_param: bool
    default_currency: str
    link_strategy: LinkStrategy
    browser_observation_allowed: bool
    parser_id: str | None
    source_type: Literal["aggregator", "carrier", "search", "deal"] = "aggregator"


def default_ru_aggregator_specs() -> tuple[RuAggregatorSpec, ...]:
    return (
        RuAggregatorSpec(
            source_id="aviasales_clickout",
            display_name="Aviasales",
            base_url="https://www.aviasales.ru/",
            allowed_hosts=("www.aviasales.ru", "aviasales.ru"),
            supports_one_way=True,
            supports_round_trip=True,
            supports_multi_city=False,
            supports_passenger_mix=False,
            supports_children=False,
            supports_infants=False,
            supports_baggage_query=False,
            supports_currency_param=True,
            default_currency="RUB",
            link_strategy="search_page",
            browser_observation_allowed=False,
            parser_id="aviasales_page",
        ),
        RuAggregatorSpec(
            source_id="travelpayouts_aviasales_deeplink",
            display_name="Aviasales partner link",
            base_url="https://www.aviasales.ru/",
            allowed_hosts=("www.aviasales.ru", "aviasales.ru"),
            supports_one_way=True,
            supports_round_trip=True,
            supports_multi_city=False,
            supports_passenger_mix=False,
            supports_children=False,
            supports_infants=False,
            supports_baggage_query=False,
            supports_currency_param=True,
            default_currency="RUB",
            link_strategy="search_page",
            browser_observation_allowed=False,
            parser_id=None,
        ),
        RuAggregatorSpec(
            source_id="yandex_travel",
            display_name="Яндекс Путешествия",
            base_url="https://travel.yandex.ru/avia/",
            allowed_hosts=("travel.yandex.ru",),
            supports_one_way=True,
            supports_round_trip=True,
            supports_multi_city=False,
            supports_passenger_mix=False,
            supports_children=False,
            supports_infants=False,
            supports_baggage_query=False,
            supports_currency_param=False,
            default_currency="RUB",
            link_strategy="search_page",
            browser_observation_allowed=True,
            parser_id="yandex_travel",
        ),
        RuAggregatorSpec(
            source_id="tutu",
            display_name="Туту",
            base_url="https://www.tutu.ru/",
            allowed_hosts=("www.tutu.ru", "tutu.ru", "avia.tutu.ru"),
            supports_one_way=True,
            supports_round_trip=True,
            supports_multi_city=False,
            supports_passenger_mix=False,
            supports_children=False,
            supports_infants=False,
            supports_baggage_query=False,
            supports_currency_param=False,
            default_currency="RUB",
            link_strategy="search_page",
            browser_observation_allowed=True,
            parser_id="tutu",
        ),
        RuAggregatorSpec(
            source_id="onetwotrip",
            display_name="OneTwoTrip",
            base_url="https://www.onetwotrip.com/",
            allowed_hosts=("www.onetwotrip.com", "onetwotrip.com"),
            supports_one_way=True,
            supports_round_trip=True,
            supports_multi_city=False,
            supports_passenger_mix=False,
            supports_children=False,
            supports_infants=False,
            supports_baggage_query=False,
            supports_currency_param=True,
            default_currency="RUB",
            link_strategy="search_page",
            browser_observation_allowed=True,
            parser_id="onetwotrip",
        ),
        RuAggregatorSpec(
            source_id="aeroflot",
            display_name="Аэрофлот",
            base_url="https://www.aeroflot.ru/",
            allowed_hosts=("www.aeroflot.ru", "aeroflot.ru"),
            supports_one_way=True,
            supports_round_trip=True,
            supports_multi_city=False,
            supports_passenger_mix=False,
            supports_children=False,
            supports_infants=False,
            supports_baggage_query=False,
            supports_currency_param=False,
            default_currency="RUB",
            link_strategy="manual",
            browser_observation_allowed=False,
            parser_id="carrier_generic",
            source_type="carrier",
        ),
        RuAggregatorSpec(
            source_id="pobeda",
            display_name="Победа",
            base_url="https://www.pobeda.aero/",
            allowed_hosts=("www.pobeda.aero", "pobeda.aero"),
            supports_one_way=True,
            supports_round_trip=True,
            supports_multi_city=False,
            supports_passenger_mix=False,
            supports_children=False,
            supports_infants=False,
            supports_baggage_query=False,
            supports_currency_param=False,
            default_currency="RUB",
            link_strategy="manual",
            browser_observation_allowed=False,
            parser_id="carrier_generic",
            source_type="carrier",
        ),
        RuAggregatorSpec(
            source_id="s7",
            display_name="S7 Airlines",
            base_url="https://www.s7.ru/",
            allowed_hosts=("www.s7.ru", "s7.ru"),
            supports_one_way=True,
            supports_round_trip=True,
            supports_multi_city=False,
            supports_passenger_mix=False,
            supports_children=False,
            supports_infants=False,
            supports_baggage_query=False,
            supports_currency_param=False,
            default_currency="RUB",
            link_strategy="manual",
            browser_observation_allowed=False,
            parser_id="carrier_generic",
            source_type="carrier",
        ),
    )
