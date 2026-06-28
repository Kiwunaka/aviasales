from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from flight_hunter.domain.offers import SearchIntent, TripType
from flight_hunter.providers.aviasales_data.client import PricesForDatesQuery


class AviasalesDataEndpoint(StrEnum):
    PRICES_FOR_DATES = "prices_for_dates"


class AviasalesDataPlanCode(StrEnum):
    PLANNED = "planned"
    UNSUPPORTED_PASSENGER_MIX = "unsupported_passenger_mix"


@dataclass(frozen=True, slots=True)
class AviasalesDataQueryPlan:
    code: AviasalesDataPlanCode
    endpoint: AviasalesDataEndpoint | None
    query: PricesForDatesQuery | None
    degraded: bool
    degraded_reason: str | None
    message: str


class AviasalesDataQueryPlanner:
    def plan(self, intent: SearchIntent, *, market: str) -> AviasalesDataQueryPlan:
        if intent.children > 0 or intent.infants > 0:
            return AviasalesDataQueryPlan(
                code=AviasalesDataPlanCode.UNSUPPORTED_PASSENGER_MIX,
                endpoint=None,
                query=None,
                degraded=False,
                degraded_reason=None,
                message="child and infant pricing is not supported by this cached adapter",
            )

        trip_type_value = intent.trip_type
        if trip_type_value is None:
            trip_type = TripType.ROUND_TRIP if intent.return_date is not None else TripType.ONE_WAY
        elif isinstance(trip_type_value, TripType):
            trip_type = trip_type_value
        else:
            trip_type = TripType(trip_type_value)
        query = PricesForDatesQuery(
            origin=intent.origin,
            destination=intent.destination,
            departure_at=intent.departure_date,
            return_at=intent.return_date,
            currency=intent.currency,
            market=market,
            one_way=trip_type == TripType.ONE_WAY,
            direct=False,
            limit=30,
            page=1,
        )
        return AviasalesDataQueryPlan(
            code=AviasalesDataPlanCode.PLANNED,
            endpoint=AviasalesDataEndpoint.PRICES_FOR_DATES,
            query=query,
            degraded=False,
            degraded_reason=None,
            message="exact-date prices_for_dates query planned",
        )
