from __future__ import annotations

from datetime import date

import pytest

from flight_hunter.application.date_matrix import DateMatrixPlanner, DateMatrixRequest


def test_round_trip_flex_three_days_creates_compatible_seven_by_seven_matrix() -> None:
    planner = DateMatrixPlanner()

    matrix = planner.plan(
        DateMatrixRequest(
            departure_date=date(2026, 10, 12),
            return_date=date(2026, 10, 19),
            flexibility_days=3,
            min_stay_days=None,
            max_stay_days=None,
        )
    )

    assert len(matrix.cells) == 49
    assert matrix.cells[0].departure_date == date(2026, 10, 9)
    assert matrix.cells[0].return_date == date(2026, 10, 16)
    assert matrix.cells[-1].departure_date == date(2026, 10, 15)
    assert matrix.cells[-1].return_date == date(2026, 10, 22)
    assert matrix.provider_calls_required == 0


def test_round_trip_matrix_filters_by_stay_length() -> None:
    planner = DateMatrixPlanner()

    matrix = planner.plan(
        DateMatrixRequest(
            departure_date=date(2026, 10, 12),
            return_date=date(2026, 10, 19),
            flexibility_days=3,
            min_stay_days=6,
            max_stay_days=8,
        )
    )

    assert matrix.cells
    assert all(6 <= cell.stay_days <= 8 for cell in matrix.cells if cell.stay_days is not None)
    assert len(matrix.cells) < 49


def test_flexibility_is_capped_to_prevent_unbounded_combinations() -> None:
    planner = DateMatrixPlanner(max_flexibility_days=7)

    with pytest.raises(ValueError, match="flexibility_days"):
        planner.plan(
            DateMatrixRequest(
                departure_date=date(2026, 10, 12),
                return_date=date(2026, 10, 19),
                flexibility_days=8,
                min_stay_days=None,
                max_stay_days=None,
            )
        )
