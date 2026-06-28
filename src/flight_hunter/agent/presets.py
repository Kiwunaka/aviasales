# ruff: noqa: RUF001

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class AgentPresetId(StrEnum):
    BUY_TIMING = "buy_timing"
    FLEXIBLE_DATES = "flexible_dates"
    NEARBY_AIRPORTS = "nearby_airports"
    HIDDEN_CITY = "hidden_city"
    SPLIT_TICKET = "split_ticket"
    ERROR_FARE_SOURCES = "error_fare_sources"
    GEO_CURRENCY = "geo_currency"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class AgentPreset:
    id: AgentPresetId
    title_ru: str
    description_ru: str
    required_slots: tuple[str, ...]
    risk_level: RiskLevel


@dataclass(frozen=True, slots=True)
class AgentPlanStep:
    action: str
    title_ru: str
    parameters: dict[str, Any]
    requires_live_refresh: bool
    explanation_ru: str


@dataclass(frozen=True, slots=True)
class AgentPlan:
    preset_id: AgentPresetId
    title_ru: str
    risk_level: RiskLevel
    missing_slots: tuple[str, ...]
    steps: tuple[AgentPlanStep, ...]
    warnings: tuple[str, ...]


class AgentPlanBuilder:
    def list_presets(self) -> tuple[AgentPreset, ...]:
        return tuple(PRESETS.values())

    def build(
        self,
        preset_id: AgentPresetId | str,
        *,
        slots: dict[str, Any],
    ) -> AgentPlan:
        preset = PRESETS[AgentPresetId(preset_id)]
        normalized_slots = {key: value for key, value in slots.items() if value not in (None, "")}
        missing_slots = tuple(
            slot for slot in preset.required_slots if slot not in normalized_slots
        )
        if missing_slots:
            return AgentPlan(
                preset_id=preset.id,
                title_ru=preset.title_ru,
                risk_level=preset.risk_level,
                missing_slots=missing_slots,
                steps=(),
                warnings=(
                    "Нужно заполнить недостающие поля. Я не буду угадывать город, дату или рейс.",
                ),
            )

        return _plan_for(preset, normalized_slots)


PRESETS: dict[AgentPresetId, AgentPreset] = {
    AgentPresetId.BUY_TIMING: AgentPreset(
        id=AgentPresetId.BUY_TIMING,
        title_ru="Когда покупать",
        description_ru="Оценить дешевые дни покупки по истории и текущим cached/live возможностям.",
        required_slots=("origin", "destination", "departure_date"),
        risk_level=RiskLevel.LOW,
    ),
    AgentPresetId.FLEXIBLE_DATES: AgentPreset(
        id=AgentPresetId.FLEXIBLE_DATES,
        title_ru="Даты +/- 3 дня",
        description_ru="Построить матрицу соседних дат и выбрать самый дешевый вариант по данным.",
        required_slots=("origin", "destination", "departure_date"),
        risk_level=RiskLevel.LOW,
    ),
    AgentPresetId.NEARBY_AIRPORTS: AgentPreset(
        id=AgentPresetId.NEARBY_AIRPORTS,
        title_ru="Аэропорты рядом",
        description_ru="Проверить аэропорты вокруг вылета и прилета в радиусе 150 км.",
        required_slots=("origin", "destination"),
        risk_level=RiskLevel.LOW,
    ),
    AgentPresetId.HIDDEN_CITY: AgentPreset(
        id=AgentPresetId.HIDDEN_CITY,
        title_ru="Скрытый город",
        description_ru=(
            "Исследовательский режим: пункт назначения как пересадка, не обычная выдача."
        ),
        required_slots=("origin", "destination", "departure_date"),
        risk_level=RiskLevel.HIGH,
    ),
    AgentPresetId.SPLIT_TICKET: AgentPreset(
        id=AgentPresetId.SPLIT_TICKET,
        title_ru="Разбить билет",
        description_ru="Сравнить один билет с отдельными сегментами и показать риски пересадки.",
        required_slots=("origin", "destination", "departure_date"),
        risk_level=RiskLevel.MEDIUM,
    ),
    AgentPresetId.ERROR_FARE_SOURCES: AgentPreset(
        id=AgentPresetId.ERROR_FARE_SOURCES,
        title_ru="Error fare источники",
        description_ru="Подобрать места для мониторинга подозрительно низких тарифов по региону.",
        required_slots=("region",),
        risk_level=RiskLevel.MEDIUM,
    ),
    AgentPresetId.GEO_CURRENCY: AgentPreset(
        id=AgentPresetId.GEO_CURRENCY,
        title_ru="Страна сайта и валюта",
        description_ru=(
            "Сравнить официальный сайт авиакомпании по странам и валютам без автопокупки."
        ),
        required_slots=("flight",),
        risk_level=RiskLevel.MEDIUM,
    ),
}


def _plan_for(preset: AgentPreset, slots: dict[str, Any]) -> AgentPlan:
    steps: tuple[AgentPlanStep, ...]
    warnings: tuple[str, ...]

    if preset.id == AgentPresetId.BUY_TIMING:
        steps = (
            AgentPlanStep(
                action="analyze_price_history",
                title_ru="Проверить историю цен",
                parameters={
                    "origin": slots["origin"],
                    "destination": slots["destination"],
                    "departure_date": slots["departure_date"],
                },
                requires_live_refresh=False,
                explanation_ru=(
                    "Сначала берем только сохраненную историю и cached данные, чтобы не выдумывать "
                    "лучшее время покупки."
                ),
            ),
            AgentPlanStep(
                action="optional_user_live_refresh",
                title_ru="Предложить ручное обновление",
                parameters={"min_gap_minutes": 10},
                requires_live_refresh=True,
                explanation_ru="Live-обновление можно запустить только кнопкой пользователя.",
            ),
        )
        warnings = ("Если истории мало, ответ будет: Недостаточно данных.",)
    elif preset.id == AgentPresetId.FLEXIBLE_DATES:
        steps = (
            AgentPlanStep(
                action="build_date_matrix",
                title_ru="Построить матрицу дат",
                parameters={
                    "origin": slots["origin"],
                    "destination": slots["destination"],
                    "departure_date": slots["departure_date"],
                    "flexibility_days": 3,
                },
                requires_live_refresh=False,
                explanation_ru="Сравниваем даты вылета в окне +/- 3 дня.",
            ),
        )
        warnings = ("Цены выводятся только с источником и временем наблюдения.",)
    elif preset.id == AgentPresetId.NEARBY_AIRPORTS:
        steps = (
            AgentPlanStep(
                action="find_nearby_airports",
                title_ru="Найти аэропорты рядом",
                parameters={
                    "origin": slots["origin"],
                    "destination": slots["destination"],
                    "radius_km": 150,
                },
                requires_live_refresh=False,
                explanation_ru=(
                    "Сначала показываем аэропорты и время на дорогу, потом сравниваем цены только "
                    "если есть данные."
                ),
            ),
        )
        warnings = ("Экономия считается вместе с оценкой наземного трансфера, когда она доступна.",)
    elif preset.id == AgentPresetId.HIDDEN_CITY:
        steps = (
            AgentPlanStep(
                action="research_hidden_city",
                title_ru="Проверить только в отдельном режиме",
                parameters={
                    "origin": slots["origin"],
                    "hidden_city": slots["destination"],
                    "departure_date": slots["departure_date"],
                    "include_in_default_ranking": False,
                },
                requires_live_refresh=True,
                explanation_ru=(
                    "Ищем маршруты, где нужный город является пересадкой, но не смешиваем их с "
                    "обычной выдачей."
                ),
            ),
        )
        warnings = (
            "Риск высокий: багаж может улететь до финального города, "
            "обратный сегмент могут отменить.",
            "Hidden-city не попадает в обычную выдачу и требует явного включения.",
        )
    elif preset.id == AgentPresetId.SPLIT_TICKET:
        steps = (
            AgentPlanStep(
                action="compare_split_ticket",
                title_ru="Сравнить единый билет и сегменты",
                parameters={
                    "origin": slots["origin"],
                    "destination": slots["destination"],
                    "departure_date": slots["departure_date"],
                    "min_connection_buffer_minutes": 180,
                },
                requires_live_refresh=False,
                explanation_ru=(
                    "Отдельные билеты показываются с риском самостоятельной пересадки и потери "
                    "защиты при задержке."
                ),
            ),
        )
        warnings = ("Разорванный билет не считается безопасной заменой единому маршруту.",)
    elif preset.id == AgentPresetId.ERROR_FARE_SOURCES:
        steps = (
            AgentPlanStep(
                action="prepare_error_fare_watchlist",
                title_ru="Подготовить список источников",
                parameters={"region": slots["region"], "requires_current_web_check": True},
                requires_live_refresh=False,
                explanation_ru=(
                    "Источники error fare быстро меняются, поэтому перед показом списка нужна "
                    "актуальная проверка."
                ),
            ),
        )
        warnings = ("Error fare показывается как подозрение, а не гарантия выписки билета.",)
    elif preset.id == AgentPresetId.GEO_CURRENCY:
        steps = (
            AgentPlanStep(
                action="compare_airline_country_currency",
                title_ru="Сравнить страны сайта и валюты",
                parameters={"flight": slots["flight"], "auto_purchase": False},
                requires_live_refresh=True,
                explanation_ru=(
                    "Сравнение делается только на официальных страницах/разрешенных API и не "
                    "оформляет покупку автоматически."
                ),
            ),
        )
        warnings = (
            "Итог нужно считать с банковской комиссией, багажом и правилами тарифа.",
            "Нельзя обходить ограничения доступа, геолокации или антибот-защиту.",
        )
    else:
        raise ValueError(f"unsupported preset: {preset.id}")

    return AgentPlan(
        preset_id=preset.id,
        title_ru=preset.title_ru,
        risk_level=preset.risk_level,
        missing_slots=(),
        steps=steps,
        warnings=warnings,
    )
