from __future__ import annotations

from flight_hunter.agent.presets import AgentPlanBuilder, AgentPresetId, RiskLevel


def test_agent_presets_include_requested_beginner_flows() -> None:
    presets = {preset.id for preset in AgentPlanBuilder().list_presets()}

    assert presets == {
        AgentPresetId.BUY_TIMING,
        AgentPresetId.FLEXIBLE_DATES,
        AgentPresetId.NEARBY_AIRPORTS,
        AgentPresetId.HIDDEN_CITY,
        AgentPresetId.SPLIT_TICKET,
        AgentPresetId.ERROR_FARE_SOURCES,
        AgentPresetId.GEO_CURRENCY,
    }


def test_flexible_dates_preset_builds_three_day_matrix_plan() -> None:
    plan = AgentPlanBuilder().build(
        AgentPresetId.FLEXIBLE_DATES,
        slots={"origin": "WAW", "destination": "BCN", "departure_date": "2026-10-12"},
    )

    assert plan.missing_slots == ()
    assert plan.risk_level == RiskLevel.LOW
    assert plan.steps[0].action == "build_date_matrix"
    assert plan.steps[0].parameters["flexibility_days"] == 3
    assert plan.steps[0].requires_live_refresh is False


def test_nearby_airports_preset_uses_beginner_default_radius() -> None:
    plan = AgentPlanBuilder().build(
        AgentPresetId.NEARBY_AIRPORTS,
        slots={"origin": "WAW", "destination": "BCN"},
    )

    assert plan.missing_slots == ()
    assert plan.steps[0].action == "find_nearby_airports"
    assert plan.steps[0].parameters["radius_km"] == 150


def test_hidden_city_preset_is_high_risk_and_never_default_ranking() -> None:
    plan = AgentPlanBuilder().build(
        AgentPresetId.HIDDEN_CITY,
        slots={"origin": "WAW", "destination": "BCN", "departure_date": "2026-10-12"},
    )

    assert plan.risk_level == RiskLevel.HIGH
    assert any("багаж" in warning.lower() for warning in plan.warnings)
    assert any("не попадает в обычную выдачу" in warning.lower() for warning in plan.warnings)
    assert plan.steps[0].parameters["include_in_default_ranking"] is False


def test_preset_reports_missing_slots_without_guessing() -> None:
    plan = AgentPlanBuilder().build(AgentPresetId.BUY_TIMING, slots={"origin": "WAW"})

    assert plan.missing_slots == ("destination", "departure_date")
    assert plan.steps == ()
    assert any("нужно заполнить" in warning.lower() for warning in plan.warnings)
