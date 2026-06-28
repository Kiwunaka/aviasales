from __future__ import annotations

from flight_hunter.domain.offers import SearchIntent, TripType
from flight_hunter.providers.aviasales_data.query_planner import (
    AviasalesDataEndpoint,
    AviasalesDataPlanCode,
    AviasalesDataQueryPlanner,
)


def test_query_planner_builds_prices_for_dates_one_way_query() -> None:
    planner = AviasalesDataQueryPlanner()

    plan = planner.plan(
        SearchIntent(
            origin="waw",
            destination="bcn",
            departure_date="2026-10-12",
            return_date=None,
            passengers=1,
            currency="rub",
            trip_type=TripType.ONE_WAY,
        ),
        market="ru",
    )

    assert plan.code == AviasalesDataPlanCode.PLANNED
    assert plan.endpoint == AviasalesDataEndpoint.PRICES_FOR_DATES
    assert plan.query is not None
    assert plan.query.origin == "WAW"
    assert plan.query.destination == "BCN"
    assert plan.query.one_way is True
    assert plan.query.return_at is None
    assert plan.degraded is False
    assert plan.degraded_reason is None


def test_query_planner_builds_prices_for_dates_round_trip_query() -> None:
    planner = AviasalesDataQueryPlanner()

    plan = planner.plan(
        SearchIntent(
            origin="WAW",
            destination="BCN",
            departure_date="2026-10-12",
            return_date="2026-10-19",
            passengers=2,
            currency="RUB",
            trip_type=TripType.ROUND_TRIP,
        ),
        market="ru",
    )

    assert plan.code == AviasalesDataPlanCode.PLANNED
    assert plan.query is not None
    assert plan.query.one_way is False
    assert plan.query.return_at == "2026-10-19"


def test_query_planner_denies_child_or_infant_pricing_until_supported() -> None:
    planner = AviasalesDataQueryPlanner()

    plan = planner.plan(
        SearchIntent(
            origin="WAW",
            destination="BCN",
            departure_date="2026-10-12",
            return_date="2026-10-19",
            passengers=3,
            currency="RUB",
            adults=2,
            children=1,
            infants=0,
        ),
        market="ru",
    )

    assert plan.code == AviasalesDataPlanCode.UNSUPPORTED_PASSENGER_MIX
    assert plan.query is None
    assert plan.message == "child and infant pricing is not supported by this cached adapter"
