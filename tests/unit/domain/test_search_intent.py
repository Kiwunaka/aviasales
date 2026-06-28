from __future__ import annotations

import pytest

from flight_hunter.domain.offers import PassengerMix, SearchIntent, TripType


def test_legacy_passenger_count_maps_to_adults_and_infers_trip_type() -> None:
    one_way = SearchIntent(
        origin="waw",
        destination="bcn",
        departure_date="2026-10-12",
        return_date=None,
        passengers=2,
        currency="rub",
    )
    round_trip = SearchIntent(
        origin="WAW",
        destination="BCN",
        departure_date="2026-10-12",
        return_date="2026-10-19",
        passengers=3,
        currency="RUB",
    )

    assert one_way.origin == "WAW"
    assert one_way.currency == "RUB"
    assert one_way.passenger_mix == PassengerMix(adults=2, children=0, infants=0)
    assert one_way.trip_type == TripType.ONE_WAY
    assert round_trip.passenger_mix == PassengerMix(adults=3, children=0, infants=0)
    assert round_trip.trip_type == TripType.ROUND_TRIP


def test_explicit_passenger_mix_must_match_total_passenger_count() -> None:
    intent = SearchIntent(
        origin="WAW",
        destination="BCN",
        departure_date="2026-10-12",
        return_date="2026-10-19",
        passengers=4,
        currency="RUB",
        adults=2,
        children=1,
        infants=1,
        trip_type=TripType.ROUND_TRIP,
    )

    assert intent.passenger_mix == PassengerMix(adults=2, children=1, infants=1)
    assert intent.passengers == 4


def test_passenger_mix_rejects_invalid_counts_and_total_mismatch() -> None:
    with pytest.raises(ValueError, match="adults must be positive"):
        PassengerMix(adults=0, children=0, infants=0)

    with pytest.raises(ValueError, match="children cannot be negative"):
        PassengerMix(adults=1, children=-1, infants=0)

    with pytest.raises(ValueError, match="passengers must match passenger mix total"):
        SearchIntent(
            origin="WAW",
            destination="BCN",
            departure_date="2026-10-12",
            return_date=None,
            passengers=2,
            currency="RUB",
            adults=1,
            children=0,
            infants=0,
        )


def test_trip_type_must_match_return_date_shape() -> None:
    with pytest.raises(ValueError, match="round trip requires return_date"):
        SearchIntent(
            origin="WAW",
            destination="BCN",
            departure_date="2026-10-12",
            return_date=None,
            passengers=1,
            currency="RUB",
            trip_type=TripType.ROUND_TRIP,
        )

    with pytest.raises(ValueError, match="one-way trip cannot have return_date"):
        SearchIntent(
            origin="WAW",
            destination="BCN",
            departure_date="2026-10-12",
            return_date="2026-10-19",
            passengers=1,
            currency="RUB",
            trip_type="one_way",
        )
