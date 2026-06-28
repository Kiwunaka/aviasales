from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True, slots=True)
class DateMatrixRequest:
    departure_date: date
    return_date: date | None
    flexibility_days: int
    min_stay_days: int | None
    max_stay_days: int | None


@dataclass(frozen=True, slots=True)
class DateMatrixCell:
    departure_date: date
    return_date: date | None
    stay_days: int | None


@dataclass(frozen=True, slots=True)
class DateMatrix:
    cells: tuple[DateMatrixCell, ...]
    provider_calls_required: int
    priced: bool


class DateMatrixPlanner:
    def __init__(self, *, max_flexibility_days: int = 7) -> None:
        self._max_flexibility_days = max_flexibility_days

    def plan(self, request: DateMatrixRequest) -> DateMatrix:
        self._validate(request)
        departure_dates = self._expanded_dates(request.departure_date, request.flexibility_days)
        return_dates = (
            self._expanded_dates(request.return_date, request.flexibility_days)
            if request.return_date is not None
            else (None,)
        )

        cells: list[DateMatrixCell] = []
        for departure_date in departure_dates:
            for return_date in return_dates:
                stay_days = (return_date - departure_date).days if return_date is not None else None
                if stay_days is not None and stay_days < 0:
                    continue
                if not self._stay_length_allowed(request, stay_days):
                    continue
                cells.append(
                    DateMatrixCell(
                        departure_date=departure_date,
                        return_date=return_date,
                        stay_days=stay_days,
                    )
                )

        return DateMatrix(cells=tuple(cells), provider_calls_required=0, priced=False)

    def _validate(self, request: DateMatrixRequest) -> None:
        if request.flexibility_days < 0:
            raise ValueError("flexibility_days cannot be negative")
        if request.flexibility_days > self._max_flexibility_days:
            raise ValueError("flexibility_days exceeds maximum")
        if request.min_stay_days is not None and request.min_stay_days < 0:
            raise ValueError("min_stay_days cannot be negative")
        if request.max_stay_days is not None and request.max_stay_days < 0:
            raise ValueError("max_stay_days cannot be negative")
        if (
            request.min_stay_days is not None
            and request.max_stay_days is not None
            and request.min_stay_days > request.max_stay_days
        ):
            raise ValueError("min_stay_days cannot exceed max_stay_days")

    @staticmethod
    def _expanded_dates(center: date, flexibility_days: int) -> tuple[date, ...]:
        return tuple(
            center + timedelta(days=offset)
            for offset in range(-flexibility_days, flexibility_days + 1)
        )

    @staticmethod
    def _stay_length_allowed(request: DateMatrixRequest, stay_days: int | None) -> bool:
        if stay_days is None:
            return True
        if request.min_stay_days is not None and stay_days < request.min_stay_days:
            return False
        return not (request.max_stay_days is not None and stay_days > request.max_stay_days)
