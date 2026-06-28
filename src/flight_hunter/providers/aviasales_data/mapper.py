from __future__ import annotations

from datetime import datetime

from flight_hunter.domain.money import Money
from flight_hunter.domain.offers import FlightOffer, Freshness
from flight_hunter.providers.aviasales_data.client import AviasalesDataItem, stable_item_id


def map_prices_for_dates_item(
    item: AviasalesDataItem,
    *,
    observed_at: datetime,
    passengers: int,
) -> FlightOffer:
    return FlightOffer(
        provider_id="aviasales_data",
        provider_offer_id=stable_item_id(item),
        origin=item.origin,
        destination=item.destination,
        departure_date=item.departure_date,
        return_date=item.return_date,
        total_price=Money(item.price_minor_units * passengers, item.currency),
        passengers=passengers,
        observed_at=observed_at,
        freshness=Freshness.CACHED,
        requires_live_confirmation=True,
        baggage_summary=None,
    )
