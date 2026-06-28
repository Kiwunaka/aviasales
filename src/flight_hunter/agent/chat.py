# ruff: noqa: RUF001

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from flight_hunter.application.airport_service import (
    AirportAutocompleteMatch,
    AirportService,
)
from flight_hunter.application.date_matrix import DateMatrixPlanner, DateMatrixRequest
from flight_hunter.application.search_service import DemoSearchService, SearchRequest
from flight_hunter.persistence.repositories import WatchRecord

_IATA_RE = re.compile(r"\b[A-ZА-Я]{3}\b", re.IGNORECASE)
_DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
_ROUTE_RE = re.compile(
    r"(?:из|с)\s+(?P<origin>.+?)\s+(?:в|до)\s+(?P<destination>.+?)(?:\s+на|\s+20\d{2}-|\s+след|\s+монитор|\s+уведом|$)",
    re.IGNORECASE,
)
_WATCH_WORDS = ("следи", "следить", "монитор", "уведом", "отслеж")


class AgentWatchCreator(Protocol):
    async def create_watch(
        self,
        *,
        household_id: UUID,
        user_id: UUID,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str | None,
    ) -> WatchRecord: ...


@dataclass(frozen=True, slots=True)
class AgentTurnRequest:
    message: str
    household_id: UUID | None = None
    user_id: UUID | None = None
    selected_origin: str | None = None
    selected_destination: str | None = None
    departure_date: str | None = None
    return_date: str | None = None
    passengers: int = 1
    adults: int | None = None
    children: int = 0
    infants: int = 0
    currency: str = "RUB"


@dataclass(frozen=True, slots=True)
class AirportOption:
    iata_code: str
    label: str
    name: str
    municipality: str
    country_code: str


@dataclass(frozen=True, slots=True)
class AgentAction:
    kind: str
    title_ru: str
    parameters: dict[str, object]
    requires_user_action: bool
    policy_decision: str
    related_id: str | None = None


@dataclass(frozen=True, slots=True)
class AgentAuditEvent:
    event_type: str
    tool_name: str
    summary: str
    policy_decision: str
    related_id: str | None = None


@dataclass(frozen=True, slots=True)
class AgentRuntimeInfo:
    backend: str
    agentic_loop: str
    model: str | None
    fallback_backend: str | None
    live_calls_allowed: bool
    cloudflare_ready: bool


@dataclass(frozen=True, slots=True)
class AgentTurnResponse:
    reply_ru: str
    extracted: dict[str, object]
    missing_slots: tuple[str, ...]
    airport_options: dict[str, tuple[AirportOption, ...]]
    actions: tuple[AgentAction, ...]
    audit_events: tuple[AgentAuditEvent, ...]
    runtime: AgentRuntimeInfo


@dataclass(slots=True)
class IntentDraft:
    origin_query: str | None = None
    destination_query: str | None = None
    origin: str | None = None
    destination: str | None = None
    departure_date: str | None = None
    return_date: str | None = None
    date_hint: str | None = None
    wants_watch: bool = False


class AgentIntentAdapter(Protocol):
    @property
    def model(self) -> str: ...

    def extract_intent(self, message: str) -> IntentDraft | None: ...


class AgentChatService:
    def __init__(
        self,
        *,
        airport_service: AirportService,
        date_matrix_planner: DateMatrixPlanner,
        search_service: DemoSearchService,
        watch_creator: AgentWatchCreator | None = None,
        intent_adapter: AgentIntentAdapter | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._airport_service = airport_service
        self._date_matrix_planner = date_matrix_planner
        self._search_service = search_service
        self._watch_creator = watch_creator
        self._intent_adapter = intent_adapter
        self._clock = clock

    async def handle_turn(self, request: AgentTurnRequest) -> AgentTurnResponse:
        draft = _parse_message(request)
        agent_draft = (
            self._intent_adapter.extract_intent(request.message) if self._intent_adapter else None
        )
        if agent_draft is not None:
            draft = _merge_drafts(base=draft, overlay=agent_draft)
        runtime = _runtime_info(self._intent_adapter)
        origin_options = _resolve_options(
            self._airport_service,
            request.selected_origin or draft.origin or draft.origin_query,
        )
        destination_options = _resolve_options(
            self._airport_service,
            request.selected_destination or draft.destination or draft.destination_query,
        )

        origin = _selected_code(request.selected_origin, draft.origin, origin_options)
        destination = _selected_code(
            request.selected_destination,
            draft.destination,
            destination_options,
        )
        departure_date = request.departure_date or draft.departure_date
        return_date = request.return_date or draft.return_date

        missing_slots = _missing_slots(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            origin_options=origin_options,
            destination_options=destination_options,
        )
        extracted = _extracted(
            draft=draft,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            request=request,
        )
        if missing_slots:
            incomplete_actions = _missing_actions(
                missing_slots=missing_slots,
                extracted=extracted,
                origin_options=origin_options,
                destination_options=destination_options,
            )
            return AgentTurnResponse(
                reply_ru=_missing_reply(missing_slots, extracted),
                extracted=extracted,
                missing_slots=missing_slots,
                airport_options={
                    "origin": tuple(_airport_option(match) for match in origin_options),
                    "destination": tuple(_airport_option(match) for match in destination_options),
                },
                actions=incomplete_actions,
                audit_events=(),
                runtime=runtime,
            )

        actions: list[AgentAction] = []
        audit_events: list[AgentAuditEvent] = []
        assert origin is not None
        assert destination is not None
        assert departure_date is not None

        search = self._search_service.search(
            SearchRequest(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                passengers=request.passengers,
                adults=request.adults,
                children=request.children,
                infants=request.infants,
                currency=request.currency,
                provider_ids=None,
                trip_type="round_trip" if return_date is not None else "one_way",
            )
        )
        actions.append(
            AgentAction(
                kind="search_cached_offers",
                title_ru="Показать cached-варианты",
                parameters={
                    "search_id": search.search_id,
                    "offers": len(search.mergeable_offers) + len(search.provider_isolated_offers),
                },
                requires_user_action=False,
                policy_decision="allowed_cached_sources_only",
                related_id=search.search_id,
            )
        )
        audit_events.append(
            _audit(
                "search_cached_offers", "allowed_cached_sources_only", search.search_id, extracted
            )
        )

        matrix = self._date_matrix_planner.plan(
            DateMatrixRequest(
                departure_date=date.fromisoformat(departure_date),
                return_date=date.fromisoformat(return_date) if return_date is not None else None,
                flexibility_days=3,
                min_stay_days=None,
                max_stay_days=None,
            )
        )
        actions.append(
            AgentAction(
                kind="build_date_matrix",
                title_ru="Проверить даты +/- 3 дня",
                parameters={"cells": len(matrix.cells), "provider_calls_required": 0},
                requires_user_action=False,
                policy_decision="allowed_no_provider_calls",
            )
        )
        audit_events.append(
            _audit("build_date_matrix", "allowed_no_provider_calls", None, extracted)
        )

        nearby = self._airport_service.nearby(origin, radius_km=150)
        actions.append(
            AgentAction(
                kind="find_nearby_airports",
                title_ru="Показать аэропорты рядом",
                parameters={
                    "origin": origin,
                    "radius_km": 150,
                    "airports": [item.airport.iata_code for item in nearby],
                },
                requires_user_action=False,
                policy_decision="allowed_reference_data_only",
            )
        )
        audit_events.append(
            _audit("find_nearby_airports", "allowed_reference_data_only", None, extracted)
        )

        if draft.wants_watch:
            watch = await self._create_watch_if_allowed(
                request=request,
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
            )
            if watch is not None:
                actions.append(
                    AgentAction(
                        kind="create_watch",
                        title_ru="Watch создан",
                        parameters={"enabled": watch.enabled},
                        requires_user_action=False,
                        policy_decision="allowed_explicit_user_intent",
                        related_id=str(watch.id),
                    )
                )
                audit_events.append(
                    _audit("create_watch", "allowed_explicit_user_intent", str(watch.id), extracted)
                )
        else:
            actions.append(
                AgentAction(
                    kind="propose_watch",
                    title_ru="Предложить watch",
                    parameters={"origin": origin, "destination": destination},
                    requires_user_action=True,
                    policy_decision="requires_explicit_user_intent",
                )
            )

        actions.append(
            AgentAction(
                kind="offer_live_check",
                title_ru="Предложить live-проверку",
                parameters={"origin": origin, "destination": destination},
                requires_user_action=True,
                policy_decision="user_action_grant_required",
            )
        )
        audit_events.append(
            _audit("offer_live_check", "user_action_grant_required", None, extracted)
        )

        return AgentTurnResponse(
            reply_ru="Я собрал безопасные действия: cached-поиск, даты +/- 3 дня и nearby 150 км.",
            extracted=extracted,
            missing_slots=(),
            airport_options={
                "origin": tuple(_airport_option(match) for match in origin_options),
                "destination": tuple(_airport_option(match) for match in destination_options),
            },
            actions=tuple(actions),
            audit_events=tuple(audit_events),
            runtime=runtime,
        )

    async def _create_watch_if_allowed(
        self,
        *,
        request: AgentTurnRequest,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str | None,
    ) -> WatchRecord | None:
        if self._watch_creator is None or request.household_id is None or request.user_id is None:
            return None
        return await self._watch_creator.create_watch(
            household_id=request.household_id,
            user_id=request.user_id,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
        )


def _parse_message(request: AgentTurnRequest) -> IntentDraft:
    message = request.message.strip()
    draft = IntentDraft(wants_watch=_contains_watch_word(message))
    draft.date_hint = _extract_date_hint(message)
    dates = _DATE_RE.findall(message)
    if dates:
        draft.departure_date = dates[0]
    if len(dates) > 1:
        draft.return_date = dates[1]

    iata_tokens = [token.upper() for token in _IATA_RE.findall(message) if token.isascii()]
    if len(iata_tokens) >= 2:
        draft.origin = iata_tokens[0]
        draft.destination = iata_tokens[1]
        return draft

    route_match = _ROUTE_RE.search(message)
    if route_match is not None:
        draft.origin_query = _canonical_city_query(route_match.group("origin"))
        draft.destination_query = _canonical_city_query(route_match.group("destination"))
    return draft


def _merge_drafts(*, base: IntentDraft, overlay: IntentDraft) -> IntentDraft:
    return IntentDraft(
        origin_query=overlay.origin_query or base.origin_query,
        destination_query=overlay.destination_query or base.destination_query,
        origin=overlay.origin or base.origin,
        destination=overlay.destination or base.destination,
        departure_date=overlay.departure_date or base.departure_date,
        return_date=overlay.return_date or base.return_date,
        date_hint=overlay.date_hint or base.date_hint,
        wants_watch=overlay.wants_watch or base.wants_watch,
    )


def _runtime_info(adapter: AgentIntentAdapter | None) -> AgentRuntimeInfo:
    if adapter is None:
        return AgentRuntimeInfo(
            backend="deterministic_harness",
            agentic_loop="policy_validated_tool_plan",
            model=None,
            fallback_backend=None,
            live_calls_allowed=False,
            cloudflare_ready=True,
        )
    return AgentRuntimeInfo(
        backend="openai_responses",
        agentic_loop="policy_validated_tool_plan",
        model=adapter.model,
        fallback_backend="deterministic_harness",
        live_calls_allowed=False,
        cloudflare_ready=True,
    )


def _resolve_options(
    airport_service: AirportService,
    query: str | None,
) -> tuple[AirportAutocompleteMatch, ...]:
    if query is None:
        return ()
    if len(query.strip()) == 3 and query.strip().isascii():
        match = airport_service.autocomplete(query.strip().upper(), limit=1)
        return match
    return airport_service.autocomplete(query, limit=6)


def _selected_code(
    selected: str | None,
    parsed_code: str | None,
    options: tuple[AirportAutocompleteMatch, ...],
) -> str | None:
    if selected:
        return selected.strip().upper()
    if parsed_code:
        return parsed_code.strip().upper()
    if len(options) == 1:
        return options[0].airport.iata_code
    return None


def _missing_slots(
    *,
    origin: str | None,
    destination: str | None,
    departure_date: str | None,
    origin_options: tuple[AirportAutocompleteMatch, ...],
    destination_options: tuple[AirportAutocompleteMatch, ...],
) -> tuple[str, ...]:
    missing: list[str] = []
    if origin is None:
        missing.append("origin" if origin_options else "origin_query")
    if destination is None:
        missing.append("destination" if destination_options else "destination_query")
    if departure_date is None:
        missing.append("departure_date")
    return tuple(missing)


def _missing_reply(missing_slots: tuple[str, ...], extracted: dict[str, object]) -> str:
    origin = _display_place(extracted.get("origin") or extracted.get("origin_query") or "откуда")
    destination = _display_place(
        extracted.get("destination") or extracted.get("destination_query") or "куда"
    )
    date_hint = extracted.get("date_hint")
    if date_hint and "departure_date" in missing_slots:
        airport_part = ""
        if "origin" in missing_slots or "destination" in missing_slots:
            airport_part = " Сначала выбери аэропорт из вариантов ниже."
        return (
            f"Понял маршрут {origin} -> {destination}. {date_hint} — это гибкий период,"
            " но я не буду угадывать конкретный день."
            f"{airport_part} Укажи дату вылета или диапазон в октябре; соседние даты +/- 3 дня"
            " проверю автоматически."
        )
    if "origin" in missing_slots or "destination" in missing_slots:
        return "Нашёл несколько вариантов, выбери аэропорт и дату, потом запущу поиск."
    return "Нужна точная дата вылета или диапазон, чтобы не угадывать маршрут."


def _display_place(value: object) -> str:
    text = str(value)
    aliases = {
        "LED": "СПб",
        "Saint Petersburg": "СПб",
        "Shanghai": "Шанхай",
    }
    return aliases.get(text, text)


def _missing_actions(
    *,
    missing_slots: tuple[str, ...],
    extracted: dict[str, object],
    origin_options: tuple[AirportAutocompleteMatch, ...],
    destination_options: tuple[AirportAutocompleteMatch, ...],
) -> tuple[AgentAction, ...]:
    actions: list[AgentAction] = []
    ambiguous_roles: list[str] = []
    if "origin" in missing_slots and origin_options:
        ambiguous_roles.append("origin")
    if "destination" in missing_slots and destination_options:
        ambiguous_roles.append("destination")
    if ambiguous_roles:
        actions.append(
            AgentAction(
                kind="clarify_airport_choice",
                title_ru="Выбрать аэропорт",
                parameters={"roles": ambiguous_roles},
                requires_user_action=True,
                policy_decision="requires_user_selection",
            )
        )
    if "departure_date" in missing_slots:
        date_hint = extracted.get("date_hint")
        title = f"Уточнить дату: {date_hint}" if date_hint else "Уточнить дату вылета"
        actions.append(
            AgentAction(
                kind="clarify_travel_dates",
                title_ru=title,
                parameters={
                    "date_hint": date_hint,
                    "default_flexibility_days": 3,
                    "provider_calls_required": 0,
                },
                requires_user_action=True,
                policy_decision="requires_exact_or_user_selected_date",
            )
        )
    return tuple(actions)


def _extracted(
    *,
    draft: IntentDraft,
    origin: str | None,
    destination: str | None,
    departure_date: str | None,
    return_date: str | None,
    request: AgentTurnRequest,
) -> dict[str, object]:
    return {
        "origin_query": draft.origin_query,
        "destination_query": draft.destination_query,
        "origin": origin,
        "destination": destination,
        "departure_date": departure_date,
        "return_date": return_date,
        "date_hint": draft.date_hint,
        "passengers": request.passengers,
        "currency": request.currency,
        "wants_watch": draft.wants_watch,
    }


def _airport_option(match: AirportAutocompleteMatch) -> AirportOption:
    airport = match.airport
    return AirportOption(
        iata_code=airport.iata_code,
        label=match.label,
        name=airport.name,
        municipality=airport.municipality,
        country_code=airport.country_code,
    )


def _audit(
    tool_name: str,
    policy_decision: str,
    related_id: str | None,
    extracted: dict[str, object],
) -> AgentAuditEvent:
    summary = (
        f"origin={extracted.get('origin')} destination={extracted.get('destination')} "
        f"departure_date={extracted.get('departure_date')} "
        f"return_date={extracted.get('return_date')} "
        f"wants_watch={extracted.get('wants_watch')}"
    )
    return AgentAuditEvent(
        event_type="agent_tool_action",
        tool_name=tool_name,
        summary=summary,
        policy_decision=policy_decision,
        related_id=related_id,
    )


def _canonical_city_query(value: str) -> str:
    normalized = value.strip().lower()
    for prefix, replacement in _CITY_ALIASES.items():
        if normalized.startswith(prefix):
            return replacement.title()
    return value.strip()


def _contains_watch_word(message: str) -> bool:
    lowered = message.lower()
    return any(word in lowered for word in _WATCH_WORDS)


def _extract_date_hint(message: str) -> str | None:
    lowered = message.lower()
    for marker, label in _MONTH_HINTS.items():
        if marker in lowered:
            return label
    return None


_CITY_ALIASES: dict[str, str] = {
    "варшав": "warsaw",
    "warszaw": "warsaw",
    "барсел": "barcelona",
    "краков": "krakow",
    "kraków": "krakow",
    "спб": "saint petersburg",
    "питер": "saint petersburg",
    "санкт-петербург": "saint petersburg",
    "санкт петербург": "saint petersburg",
    "st petersburg": "saint petersburg",
    "saint petersburg": "saint petersburg",
    "шанха": "shanghai",
    "shanghai": "shanghai",
    "лодз": "lodz",
    "łodz": "lodz",
    "łódź": "lodz",
}

_MONTH_HINTS: dict[str, str] = {
    "январ": "январь",
    "феврал": "февраль",
    "март": "март",
    "апрел": "апрель",
    "мая": "май",
    "май": "май",
    "июн": "июнь",
    "июл": "июль",
    "август": "август",
    "сентябр": "сентябрь",
    "октябр": "октябрь",
    "ноябр": "ноябрь",
    "декабр": "декабрь",
    "january": "January",
    "february": "February",
    "march": "March",
    "april": "April",
    "may": "May",
    "june": "June",
    "july": "July",
    "august": "August",
    "september": "September",
    "october": "October",
    "november": "November",
    "december": "December",
}
