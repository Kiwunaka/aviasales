from __future__ import annotations

from flight_hunter.application.airport_service import AirportService
from flight_hunter.geo.demo_repository import DemoAirportRepository


def test_autocomplete_finds_city_and_iata_matches() -> None:
    service = AirportService(repository=DemoAirportRepository())

    matches = service.autocomplete("wars")

    assert [match.airport.iata_code for match in matches[:2]] == ["WAW", "WMI"]
    assert matches[0].label == "WAW - Warsaw Chopin Airport, Warsaw"


def test_autocomplete_understands_spb_and_shanghai_aliases() -> None:
    service = AirportService(repository=DemoAirportRepository())

    origin_matches = service.autocomplete("спб")
    destination_matches = service.autocomplete("Шанхай")

    assert [match.airport.iata_code for match in origin_matches] == ["LED"]
    assert [match.airport.iata_code for match in destination_matches[:2]] == ["PVG", "SHA"]


def test_nearby_returns_distances_without_claiming_airfare_savings() -> None:
    service = AirportService(repository=DemoAirportRepository())

    nearby = service.nearby("WAW", radius_km=150)

    codes = [item.airport.iata_code for item in nearby]
    assert codes == ["WMI", "LCJ"]
    assert nearby[0].distance_km == 38
    assert nearby[0].transfer_note == "Approximate distance only; airfare savings are not implied."
