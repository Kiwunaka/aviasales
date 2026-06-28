from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from flight_hunter.geo.airports import Airport, distance_km


class AirportRepository(Protocol):
    def all(self) -> tuple[Airport, ...]: ...

    def get(self, iata_code: str) -> Airport | None: ...


@dataclass(frozen=True, slots=True)
class AirportAutocompleteMatch:
    airport: Airport
    label: str


@dataclass(frozen=True, slots=True)
class NearbyAirport:
    airport: Airport
    distance_km: int
    transfer_note: str


class AirportService:
    def __init__(self, *, repository: AirportRepository) -> None:
        self._repository = repository

    def autocomplete(self, query: str, *, limit: int = 8) -> tuple[AirportAutocompleteMatch, ...]:
        normalized_query = normalize_airport_query(query)
        if len(normalized_query) < 2:
            return ()

        matches: list[AirportAutocompleteMatch] = []
        for airport in self._repository.all():
            if not airport.is_searchable:
                continue
            haystack = _airport_search_text(airport)
            if normalized_query in haystack:
                matches.append(
                    AirportAutocompleteMatch(
                        airport=airport,
                        label=f"{airport.iata_code} - {airport.name}, {airport.municipality}",
                    )
                )

        matches.sort(key=lambda match: self._autocomplete_sort_key(match, normalized_query))
        return tuple(matches[:limit])

    def nearby(self, iata_code: str, *, radius_km: int) -> tuple[NearbyAirport, ...]:
        if radius_km < 1:
            raise ValueError("radius_km must be positive")
        origin = self._repository.get(iata_code)
        if origin is None:
            return ()

        nearby: list[NearbyAirport] = []
        for airport in self._repository.all():
            if airport.iata_code == origin.iata_code or not airport.is_searchable:
                continue
            distance = distance_km(origin, airport)
            if distance <= radius_km:
                nearby.append(
                    NearbyAirport(
                        airport=airport,
                        distance_km=distance,
                        transfer_note=(
                            "Approximate distance only; airfare savings are not implied."
                        ),
                    )
                )

        nearby.sort(key=lambda item: (item.distance_km, item.airport.iata_code))
        return tuple(nearby)

    @staticmethod
    def _autocomplete_sort_key(
        match: AirportAutocompleteMatch,
        normalized_query: str,
    ) -> tuple[int, str]:
        airport = match.airport
        if airport.iata_code.lower().startswith(normalized_query):
            priority = 0
        elif airport.municipality.lower().startswith(normalized_query):
            priority = 1
        else:
            priority = 2
        return (priority, airport.iata_code)


def normalize_airport_query(query: str) -> str:
    normalized = query.strip().lower()
    for prefix, replacement in _CITY_ALIASES.items():
        if normalized.startswith(prefix):
            return replacement
    return normalized


def _airport_search_text(airport: Airport) -> str:
    return " ".join(
        (
            airport.iata_code,
            airport.name,
            airport.municipality,
            *airport.keywords,
        )
    ).lower()


_CITY_ALIASES: dict[str, str] = {
    "варшав": "warsaw",
    "warszaw": "warsaw",
    "барсел": "barcelona",
    "краков": "krakow",
    "krakow": "krakow",
    "спб": "saint petersburg",
    "питер": "saint petersburg",
    "санкт-петербург": "saint petersburg",
    "санкт петербург": "saint petersburg",
    "st petersburg": "saint petersburg",
    "saint petersburg": "saint petersburg",
    "шанха": "shanghai",
    "shanghai": "shanghai",
    "kraków": "krakow",
    "лодз": "lodz",
    "łodz": "lodz",
    "łódź": "lodz",
}
