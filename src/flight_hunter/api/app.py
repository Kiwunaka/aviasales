from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from flight_hunter.agent.chat import (
    AgentAction,
    AgentAuditEvent,
    AgentChatService,
    AgentIntentAdapter,
    AgentRuntimeInfo,
    AgentTurnRequest,
    AgentTurnResponse,
    AirportOption,
)
from flight_hunter.agent.openai_responses import OpenAIResponsesAgentAdapter
from flight_hunter.agent.presets import AgentPlan, AgentPlanBuilder, AgentPlanStep, AgentPreset
from flight_hunter.api.web import render_index_html
from flight_hunter.application.airport_service import (
    AirportAutocompleteMatch,
    AirportService,
    NearbyAirport,
)
from flight_hunter.application.date_matrix import (
    DateMatrix,
    DateMatrixCell,
    DateMatrixPlanner,
    DateMatrixRequest,
)
from flight_hunter.application.durable_live_observations import DurableLiveObservationService
from flight_hunter.application.live_observations import BrowserSourceCatalog, GrantSource
from flight_hunter.application.price_sources import PriceSource, PriceSourceCatalog
from flight_hunter.application.provider_registry import ProviderRegistry, ProviderStatus
from flight_hunter.application.search_service import DemoSearchService, SearchRequest, SearchResult
from flight_hunter.application.source_contracts import SourceContractCatalog, SourceReadiness
from flight_hunter.application.watch_service import CreateWatchCommand, WatchService
from flight_hunter.config import AppSettings, load_env_file
from flight_hunter.domain.money import Money
from flight_hunter.domain.observation import BrowserSource, LiveObservation
from flight_hunter.domain.offers import FlightOffer, SearchIntent
from flight_hunter.domain.policy import ExecutionContext
from flight_hunter.domain.ranking import offer_ranking_key
from flight_hunter.domain.search_results import (
    BrowserObservedOffer,
    Confidence,
    DealCandidate,
    ExternalSearchLink,
    FreshnessSummary,
)
from flight_hunter.geo.demo_repository import DemoAirportRepository
from flight_hunter.notifications.telegram import (
    TelegramWebhookDecisionCode,
    TelegramWebhookHandler,
)
from flight_hunter.persistence.repositories import (
    AgentAuditRepository,
    AirportReferenceRepository,
    AirportSearchMatch,
    HouseholdWatchRepository,
    LiveObservationRepository,
    NewAgentAuditEvent,
    TelegramUpdateRepository,
    WatchRecord,
)
from flight_hunter.providers.aviasales_data.adapter import AviasalesDataAdapter
from flight_hunter.providers.aviasales_data.client import AviasalesDataClient


class HealthResponse(BaseModel):
    app: str
    status: str
    external_credentials_required: bool


class ProviderStatusResponse(BaseModel):
    provider_id: str
    enabled: bool
    credentials_present: bool
    access_approved: bool
    data_kind: str
    merge_scope: str
    background_requests_allowed: bool
    user_action_required: bool
    blocked_reasons: list[str]
    notes: str


class ProvidersResponse(BaseModel):
    providers: list[ProviderStatusResponse]


class AdminProviderHealthItemResponse(BaseModel):
    provider_id: str
    enabled: bool
    credentials_present: bool
    secret_present: bool
    access_approved: bool
    data_kind: str
    background_requests_allowed: bool
    blocked_reasons: list[str]


class AdminProviderHealthResponse(BaseModel):
    checked_at: str
    providers: list[AdminProviderHealthItemResponse]


class PriceSourceResponse(BaseModel):
    id: str
    name: str
    source_type: str
    price_kind: str
    supports_rub: bool
    in_app_booking: bool
    purchase_flow: str
    requires_manual_confirmation: bool
    setup_required_ru: str
    notes_ru: str


class PriceSourcesResponse(BaseModel):
    strategy: str
    sources: list[PriceSourceResponse]


class SourceContractResponse(BaseModel):
    source_id: str
    display_name: str
    stage: str
    adapter_module: str | None
    contract_file: str
    terms_url: str
    required_env: list[str]
    operations: list[str]
    invariants: list[str]
    notes: str
    enabled: bool
    credentials_present: bool
    access_approved: bool
    data_kind: str
    merge_scope: str
    background_requests_allowed: bool
    user_action_required: bool
    blocked_reasons: list[str]


class SourceContractSummaryResponse(BaseModel):
    total: int
    implemented: int
    policy_skeleton: int
    contract_only: int


class SourceContractsResponse(BaseModel):
    summary: SourceContractSummaryResponse
    sources: list[SourceContractResponse]


class BrowserSourceResponse(BaseModel):
    source_id: str
    display_name: str
    enabled: bool
    permission_status: str
    user_action_required: bool
    background_allowed: bool
    supported_routes: list[str]
    current_health: str


class BrowserSourcesResponse(BaseModel):
    sources: list[BrowserSourceResponse]


class SearchRequestBody(BaseModel):
    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    departure_date: str
    return_date: str | None = None
    passengers: int = Field(ge=1)
    adults: int | None = Field(default=None, ge=1)
    children: int = Field(default=0, ge=0)
    infants: int = Field(default=0, ge=0)
    trip_type: str | None = Field(default=None, pattern="^(one_way|round_trip)$")
    currency: str = Field(min_length=3, max_length=3)
    provider_ids: list[str] | None = None

    @model_validator(mode="after")
    def validate_passenger_mix_and_trip_type(self) -> SearchRequestBody:
        adults = self.adults if self.adults is not None else self.passengers
        if adults + self.children + self.infants != self.passengers:
            raise ValueError("passengers must match adults + children + infants")
        if self.trip_type == "round_trip" and self.return_date is None:
            raise ValueError("round_trip requires return_date")
        if self.trip_type == "one_way" and self.return_date is not None:
            raise ValueError("one_way cannot include return_date")
        return self


class AgentModeResponse(BaseModel):
    enabled: bool
    provider: str
    mcp_enabled: bool
    mcp_server_configured: bool


class AgentPresetResponse(BaseModel):
    id: str
    title_ru: str
    description_ru: str
    required_slots: list[str]
    risk_level: str


class AgentPresetsResponse(BaseModel):
    mode: AgentModeResponse
    presets: list[AgentPresetResponse]


class AgentPlanRequestBody(BaseModel):
    preset_id: str
    slots: dict[str, object] = Field(default_factory=dict)


class AgentPlanStepResponse(BaseModel):
    action: str
    title_ru: str
    parameters: dict[str, object]
    requires_live_refresh: bool
    explanation_ru: str


class AgentPlanResponse(BaseModel):
    preset_id: str
    title_ru: str
    risk_level: str
    missing_slots: list[str]
    steps: list[AgentPlanStepResponse]
    warnings: list[str]


class AgentChatTurnRequestBody(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    selected_origin: str | None = Field(default=None, min_length=3, max_length=3)
    selected_destination: str | None = Field(default=None, min_length=3, max_length=3)
    departure_date: str | None = None
    return_date: str | None = None
    passengers: int = Field(default=1, ge=1)
    adults: int | None = Field(default=None, ge=1)
    children: int = Field(default=0, ge=0)
    infants: int = Field(default=0, ge=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)


class AgentAirportOptionResponse(BaseModel):
    iata_code: str
    label: str
    name: str
    municipality: str
    country_code: str


class AgentActionResponse(BaseModel):
    kind: str
    title_ru: str
    parameters: dict[str, object]
    requires_user_action: bool
    policy_decision: str
    related_id: str | None


class AgentAuditEventResponse(BaseModel):
    event_type: str
    tool_name: str
    summary: str
    policy_decision: str
    related_id: str | None


class AgentRuntimeResponse(BaseModel):
    backend: str
    agentic_loop: str
    model: str | None
    fallback_backend: str | None
    live_calls_allowed: bool
    cloudflare_ready: bool


class AgentChatTurnResponse(BaseModel):
    reply_ru: str
    extracted: dict[str, object]
    missing_slots: list[str]
    airport_options: dict[str, list[AgentAirportOptionResponse]]
    actions: list[AgentActionResponse]
    audit_events: list[AgentAuditEventResponse]
    runtime: AgentRuntimeResponse


class MoneyResponse(BaseModel):
    minor_units: int
    currency: str
    formatted: str


class OfferResponse(BaseModel):
    provider_id: str
    provider_offer_id: str
    origin: str
    destination: str
    departure_date: str
    return_date: str | None
    total_price: MoneyResponse
    passengers: int
    observed_at: str
    freshness: str
    requires_live_confirmation: bool
    baggage_summary: str | None
    ranking_reasons: list[str]


class ExternalSearchLinkResponse(BaseModel):
    kind: str
    source_id: str
    source_name: str
    url: str
    origin: str
    destination: str
    departure_date: str
    return_date: str | None
    passengers: int
    adults: int
    children: int
    infants: int
    currency: str
    source_type: str
    purchase_flow: str
    price_known: bool
    requires_external_confirmation: bool
    notes_ru: str | None
    warnings: list[str]


class BrowserObservedOfferResponse(BaseModel):
    kind: str
    observation_id: str
    source_id: str
    source_name: str
    provider_offer_id: str
    origin: str
    destination: str
    departure_date: str | None
    return_date: str | None
    total_price: MoneyResponse | None
    passengers: int
    observed_at: str
    final_url: str
    display_url: str
    freshness: str
    confidence: str
    parser_version: str
    parser_warnings: list[str]
    airline_name: str | None
    airline_iata: str | None
    flight_number: str | None
    departure_time_local: str | None
    arrival_time_local: str | None
    duration_minutes: int | None
    stops: int | None
    baggage_summary: str | None
    seller_name: str | None
    requires_external_confirmation: bool


class DealCandidateResponse(BaseModel):
    kind: str
    source_id: str
    url: str
    title: str
    summary_ru: str
    extracted_price: MoneyResponse | None
    extracted_origin: str | None
    extracted_destination: str | None
    extracted_date_window: str | None
    confidence: str
    discovered_at: str
    requires_manual_verification: bool


class FreshnessSummaryResponse(BaseModel):
    best_price_source: str | None
    freshest_observation_at: str | None
    needs_external_confirmation: bool


class ProviderDenialResponse(BaseModel):
    code: str
    message: str


class SearchResponse(BaseModel):
    search_id: str
    offers: list[OfferResponse]
    priced_offers: list[OfferResponse]
    provider_isolated_offers: list[OfferResponse]
    browser_observed_offers: list[BrowserObservedOfferResponse]
    external_links: list[ExternalSearchLinkResponse]
    deal_candidates: list[DealCandidateResponse]
    denied_providers: dict[str, ProviderDenialResponse]
    warnings: list[str]
    freshness_summary: FreshnessSummaryResponse


class LiveObservationGrantRequestBody(BaseModel):
    source_id: str
    search_intent: SearchRequestBody


class LiveObservationGrantResponse(BaseModel):
    source_id: str
    grant_token: str
    expires_at: str


class LiveObservationCreateRequestBody(BaseModel):
    source_id: str
    search_intent: SearchRequestBody
    grant_token: str


class LiveObservationCreateResponse(BaseModel):
    observation_id: str
    status: str


class LiveObservationResponse(BaseModel):
    observation_id: str
    source_id: str
    status: str
    result_scope: str
    observed_at: str | None
    offers: list[OfferResponse]
    error_code: str | None
    error_message: str | None


class AirportAutocompleteItemResponse(BaseModel):
    iata_code: str
    name: str
    municipality: str
    country_code: str
    label: str


class AirportAutocompleteResponse(BaseModel):
    airports: list[AirportAutocompleteItemResponse]


class AirportImportStatusResponse(BaseModel):
    source: str
    imported_at: str | None
    rows_imported: int | None


class AirportSearchResponse(BaseModel):
    airports: list[AirportAutocompleteItemResponse]
    import_status: AirportImportStatusResponse


class NearbyAirportResponse(BaseModel):
    iata_code: str
    name: str
    municipality: str
    country_code: str
    distance_km: int
    transfer_note: str


class NearbyAirportsResponse(BaseModel):
    airports: list[NearbyAirportResponse]


class DateMatrixRequestBody(BaseModel):
    departure_date: date
    return_date: date | None = None
    flexibility_days: int = Field(ge=0, le=7)
    min_stay_days: int | None = Field(default=None, ge=0)
    max_stay_days: int | None = Field(default=None, ge=0)


class DateMatrixCellResponse(BaseModel):
    departure_date: str
    return_date: str | None
    stay_days: int | None


class DateMatrixResponse(BaseModel):
    cells: list[DateMatrixCellResponse]
    provider_calls_required: int
    priced: bool


class TelegramWebhookResponse(BaseModel):
    code: str
    status: str


class WatchCreateRequestBody(BaseModel):
    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    departure_date: str
    return_date: str | None = None


class WatchResponse(BaseModel):
    id: str
    household_id: str
    owner_user_id: str
    origin: str
    destination: str
    departure_date: str
    return_date: str | None
    enabled: bool
    created_at: str


class WatchesResponse(BaseModel):
    watches: list[WatchResponse]


def create_app(
    *,
    watch_session_factory: async_sessionmaker[AsyncSession] | None = None,
    settings: AppSettings | None = None,
    agent_intent_adapter: AgentIntentAdapter | None = None,
) -> FastAPI:
    load_env_file()
    settings = settings or AppSettings.from_env()
    app = FastAPI(title="Flight Hunter", version="0.1.0")
    registry = ProviderRegistry.default(clock=lambda: datetime.now(UTC), settings=settings)
    provider_instances = _provider_instances(settings)
    search_service = DemoSearchService(
        registry=registry,
        clock=lambda: datetime.now(UTC),
        providers=provider_instances,
        enabled_external_source_ids=settings.ru_clickout_enabled_source_ids,
    )
    agent_plan_builder = AgentPlanBuilder()
    airport_service = AirportService(repository=DemoAirportRepository())
    date_matrix_planner = DateMatrixPlanner()
    intent_adapter = agent_intent_adapter or _agent_intent_adapter(settings)
    price_source_catalog = PriceSourceCatalog.default()
    source_contract_catalog = SourceContractCatalog.default(settings=settings, registry=registry)
    browser_source_catalog = BrowserSourceCatalog.demo(
        enabled=settings.scraping_observer_enabled,
        clock=lambda: datetime.now(UTC),
    )
    telegram_webhook_handler = TelegramWebhookHandler(
        enabled=settings.telegram_enabled,
        secret_token=settings.telegram_webhook_secret,
    )
    session_factory = watch_session_factory or _watch_session_factory(settings.database_url)

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        return HTMLResponse(render_index_html())

    @app.get("/healthz", response_model=HealthResponse)
    def healthz() -> HealthResponse:
        return HealthResponse(
            app="Flight Hunter",
            status="ok",
            external_credentials_required=False,
        )

    @app.get("/api/v1/providers", response_model=ProvidersResponse)
    def providers() -> ProvidersResponse:
        return ProvidersResponse(
            providers=[_provider_status_response(status) for status in registry.statuses()]
        )

    @app.get("/api/v1/admin/providers/health", response_model=AdminProviderHealthResponse)
    def admin_provider_health() -> AdminProviderHealthResponse:
        return AdminProviderHealthResponse(
            checked_at=datetime.now(UTC).isoformat(),
            providers=[_admin_provider_health_response(status) for status in registry.statuses()],
        )

    @app.get("/api/v1/price-sources", response_model=PriceSourcesResponse)
    def price_sources() -> PriceSourcesResponse:
        return PriceSourcesResponse(
            strategy="external_clickout",
            sources=[_price_source_response(source) for source in price_source_catalog.sources],
        )

    @app.get("/api/v1/source-contracts", response_model=SourceContractsResponse)
    def source_contracts() -> SourceContractsResponse:
        sources = source_contract_catalog.readiness()
        return SourceContractsResponse(
            summary=_source_contract_summary_response(sources),
            sources=[_source_contract_response(source) for source in sources],
        )

    @app.get("/api/v1/browser-sources", response_model=BrowserSourcesResponse)
    def browser_sources() -> BrowserSourcesResponse:
        now = datetime.now(UTC)
        return BrowserSourcesResponse(
            sources=[
                _browser_source_response(source, now=now)
                for source in browser_source_catalog.sources()
            ],
        )

    @app.get("/api/v1/agent/presets", response_model=AgentPresetsResponse)
    def agent_presets() -> AgentPresetsResponse:
        return AgentPresetsResponse(
            mode=_agent_mode_response(settings),
            presets=[
                _agent_preset_response(preset) for preset in agent_plan_builder.list_presets()
            ],
        )

    @app.post("/api/v1/agent/plan", response_model=AgentPlanResponse)
    def agent_plan(body: AgentPlanRequestBody) -> AgentPlanResponse:
        try:
            plan = agent_plan_builder.build(body.preset_id, slots=body.slots)
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="unknown agent preset") from exc
        return _agent_plan_response(plan)

    @app.post("/api/v1/agent/chat/turn", response_model=AgentChatTurnResponse)
    async def agent_chat_turn(
        body: AgentChatTurnRequestBody,
        household_header: str | None = Header(
            default=None,
            alias="X-Flight-Hunter-Household-Id",
        ),
        user_header: str | None = Header(
            default=None,
            alias="X-Flight-Hunter-User-Id",
        ),
    ) -> AgentChatTurnResponse:
        household_id = _household_context(household_header)
        user_id = _user_context(user_header)
        async with session_factory() as session:
            service = AgentChatService(
                airport_service=airport_service,
                date_matrix_planner=date_matrix_planner,
                search_service=search_service,
                watch_creator=_AgentWatchCreator(session),
                intent_adapter=intent_adapter,
                clock=lambda: datetime.now(UTC),
            )
            response = await service.handle_turn(
                AgentTurnRequest(
                    message=body.message,
                    household_id=household_id,
                    user_id=user_id,
                    selected_origin=body.selected_origin,
                    selected_destination=body.selected_destination,
                    departure_date=body.departure_date,
                    return_date=body.return_date,
                    passengers=body.passengers,
                    adults=body.adults,
                    children=body.children,
                    infants=body.infants,
                    currency=body.currency,
                )
            )
            audit_repository = AgentAuditRepository(session)
            for event in response.audit_events:
                await audit_repository.add_event(
                    NewAgentAuditEvent(
                        id=uuid4(),
                        household_id=household_id,
                        user_id=user_id,
                        event_type=event.event_type,
                        tool_name=event.tool_name,
                        summary=event.summary,
                        policy_decision=event.policy_decision,
                        related_id=event.related_id,
                        created_at=datetime.now(UTC),
                    )
                )
            await session.commit()
        return _agent_chat_turn_response(response)

    @app.post("/api/v1/searches", response_model=SearchResponse, status_code=201)
    def searches(body: SearchRequestBody) -> SearchResponse:
        result = search_service.search(
            SearchRequest(
                origin=body.origin,
                destination=body.destination,
                departure_date=body.departure_date,
                return_date=body.return_date,
                passengers=body.passengers,
                currency=body.currency,
                provider_ids=tuple(body.provider_ids) if body.provider_ids is not None else None,
                adults=body.adults,
                children=body.children,
                infants=body.infants,
                trip_type=body.trip_type,
            )
        )
        return _search_response(result)

    @app.post(
        "/api/v1/live-observation-grants",
        response_model=LiveObservationGrantResponse,
        status_code=201,
    )
    async def issue_live_observation_grant(
        body: LiveObservationGrantRequestBody,
        user_header: str | None = Header(
            default=None,
            alias="X-Flight-Hunter-User-Id",
        ),
    ) -> LiveObservationGrantResponse | JSONResponse:
        user_id = _user_context(user_header)
        if user_id is None:
            return _auth_context_missing_response()
        async with session_factory() as session:
            service = DurableLiveObservationService(
                catalog=browser_source_catalog,
                repository=LiveObservationRepository(session),
                clock=lambda: datetime.now(UTC),
                grant_ttl=timedelta(minutes=5),
            )
            decision = await service.issue_grant(
                user_id=user_id,
                source_id=body.source_id,
                search_intent=_search_intent_from_body(body.search_intent),
                source=GrantSource.WEB_CLICK,
            )
            await session.commit()
        if not decision.allowed or decision.grant_token is None or decision.expires_at is None:
            return _coded_error_response(
                status_code=403,
                code=decision.code.value,
                message=decision.message,
            )
        return LiveObservationGrantResponse(
            source_id=body.source_id,
            grant_token=decision.grant_token,
            expires_at=decision.expires_at.isoformat(),
        )

    @app.post(
        "/api/v1/live-observations",
        response_model=LiveObservationCreateResponse,
        status_code=202,
    )
    async def create_live_observation(
        body: LiveObservationCreateRequestBody,
        user_header: str | None = Header(
            default=None,
            alias="X-Flight-Hunter-User-Id",
        ),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> LiveObservationCreateResponse | JSONResponse:
        user_id = _user_context(user_header)
        if user_id is None:
            return _auth_context_missing_response()
        if idempotency_key is None or not idempotency_key.strip():
            return _coded_error_response(
                status_code=400,
                code="idempotency_key_required",
                message="Idempotency-Key header is required",
            )
        async with session_factory() as session:
            service = DurableLiveObservationService(
                catalog=browser_source_catalog,
                repository=LiveObservationRepository(session),
                clock=lambda: datetime.now(UTC),
            )
            decision = await service.create_observation(
                user_id=user_id,
                source_id=body.source_id,
                search_intent=_search_intent_from_body(body.search_intent),
                grant_token=body.grant_token,
                idempotency_key=idempotency_key,
                context=ExecutionContext.WEB_USER_ACTION,
            )
            await session.commit()
        if not decision.accepted or decision.observation_id is None:
            return _coded_error_response(
                status_code=403,
                code=decision.code.value,
                message=decision.message,
            )
        return LiveObservationCreateResponse(
            observation_id=str(decision.observation_id),
            status=decision.initial_status.value if decision.initial_status is not None else "",
        )

    @app.get(
        "/api/v1/live-observations/{observation_id}",
        response_model=LiveObservationResponse,
    )
    async def get_live_observation(
        observation_id: UUID,
        user_header: str | None = Header(
            default=None,
            alias="X-Flight-Hunter-User-Id",
        ),
    ) -> LiveObservationResponse | JSONResponse:
        user_id = _user_context(user_header)
        if user_id is None:
            return _auth_context_missing_response()
        async with session_factory() as session:
            service = DurableLiveObservationService(
                catalog=browser_source_catalog,
                repository=LiveObservationRepository(session),
                clock=lambda: datetime.now(UTC),
            )
            observation = await service.get_observation(
                user_id=user_id,
                observation_id=observation_id,
            )
        if observation is None:
            return _coded_error_response(
                status_code=404,
                code="observation_not_found",
                message="live observation not found",
            )
        return _live_observation_response(observation)

    @app.get("/api/v1/airports/autocomplete", response_model=AirportAutocompleteResponse)
    def airport_autocomplete(q: str) -> AirportAutocompleteResponse:
        return AirportAutocompleteResponse(
            airports=[
                _airport_autocomplete_response(match) for match in airport_service.autocomplete(q)
            ]
        )

    @app.get("/api/v1/airports/search", response_model=AirportSearchResponse)
    async def airport_search(q: str) -> AirportSearchResponse:
        try:
            async with session_factory() as session:
                repository = AirportReferenceRepository(session)
                import_run = await repository.latest_import_run()
                if import_run is not None:
                    matches = await repository.search(q)
                    return AirportSearchResponse(
                        airports=[_airport_search_match_response(match) for match in matches],
                        import_status=AirportImportStatusResponse(
                            source=import_run.source,
                            imported_at=import_run.imported_at.isoformat(),
                            rows_imported=import_run.rows_imported,
                        ),
                    )
        except SQLAlchemyError:
            fallback_source = "demo"
        else:
            fallback_source = "demo"

        return AirportSearchResponse(
            airports=[
                _airport_autocomplete_response(match) for match in airport_service.autocomplete(q)
            ],
            import_status=AirportImportStatusResponse(
                source=fallback_source,
                imported_at=None,
                rows_imported=None,
            ),
        )

    @app.get("/api/v1/airports/nearby", response_model=NearbyAirportsResponse)
    def airport_nearby(iata_code: str, radius_km: int = 150) -> NearbyAirportsResponse:
        return NearbyAirportsResponse(
            airports=[
                _nearby_airport_response(airport)
                for airport in airport_service.nearby(iata_code, radius_km=radius_km)
            ]
        )

    @app.post("/api/v1/searches/date-matrix", response_model=DateMatrixResponse)
    def date_matrix(body: DateMatrixRequestBody) -> DateMatrixResponse:
        matrix = date_matrix_planner.plan(
            DateMatrixRequest(
                departure_date=body.departure_date,
                return_date=body.return_date,
                flexibility_days=body.flexibility_days,
                min_stay_days=body.min_stay_days,
                max_stay_days=body.max_stay_days,
            )
        )
        return _date_matrix_response(matrix)

    @app.post("/api/v1/watches", response_model=WatchResponse, status_code=201)
    async def create_watch(
        body: WatchCreateRequestBody,
        household_header: str | None = Header(
            default=None,
            alias="X-Flight-Hunter-Household-Id",
        ),
        user_header: str | None = Header(
            default=None,
            alias="X-Flight-Hunter-User-Id",
        ),
    ) -> WatchResponse | JSONResponse:
        auth_context = _auth_context(household_header, user_header)
        if auth_context is None:
            return _auth_context_missing_response()
        household_id, user_id = auth_context
        async with session_factory() as session:
            service = WatchService(HouseholdWatchRepository(session))
            watch = await service.create_watch(
                CreateWatchCommand(
                    household_id=household_id,
                    owner_user_id=user_id,
                    origin=body.origin,
                    destination=body.destination,
                    departure_date=body.departure_date,
                    return_date=body.return_date,
                )
            )
            await session.commit()
        return _watch_response(watch)

    @app.get("/api/v1/watches", response_model=WatchesResponse)
    async def watches(
        household_header: str | None = Header(
            default=None,
            alias="X-Flight-Hunter-Household-Id",
        ),
        user_header: str | None = Header(
            default=None,
            alias="X-Flight-Hunter-User-Id",
        ),
    ) -> WatchesResponse | JSONResponse:
        auth_context = _auth_context(household_header, user_header)
        if auth_context is None:
            return _auth_context_missing_response()
        household_id, _user_id = auth_context
        async with session_factory() as session:
            service = WatchService(HouseholdWatchRepository(session))
            records = await service.list_watches(household_id)
        return WatchesResponse(watches=[_watch_response(record) for record in records])

    @app.post(
        "/api/v1/telegram/webhook",
        response_model=TelegramWebhookResponse,
    )
    async def telegram_webhook(
        body: dict[str, object],
        x_telegram_secret: str | None = Header(
            default=None,
            alias="X-Telegram-Bot-Api-Secret-Token",
        ),
    ) -> JSONResponse:
        decision = telegram_webhook_handler.handle_update(
            provided_secret=x_telegram_secret,
            update=body,
        )
        code = decision.code
        if code == TelegramWebhookDecisionCode.ACCEPTED:
            update_id = _telegram_update_id(body)
            if update_id is None:
                code = TelegramWebhookDecisionCode.INVALID_UPDATE
            else:
                async with session_factory() as session:
                    repository = TelegramUpdateRepository(session)
                    recorded = await repository.record_update(
                        update_id=update_id,
                        received_at=datetime.now(UTC),
                    )
                    await session.commit()
                if not recorded:
                    code = TelegramWebhookDecisionCode.DUPLICATE

        status_code, status = _telegram_response_status(code)
        return JSONResponse(
            status_code=status_code,
            content={"code": code.value, "status": status},
        )

    return app


def _watch_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(database_url)
    return async_sessionmaker(engine, expire_on_commit=False)


def _provider_instances(settings: AppSettings) -> dict[str, AviasalesDataAdapter]:
    if settings.travelpayouts_api_token is None:
        return {}
    return {
        "aviasales_data": AviasalesDataAdapter(
            client=AviasalesDataClient(token=settings.travelpayouts_api_token),
            enabled=settings.aviasales_data_enabled,
            credentials_present=settings.aviasales_data_credentials_present,
            market=settings.aviasales_data_default_market,
            internal_rpm=settings.aviasales_data_internal_rpm,
            clock=lambda: datetime.now(UTC),
        )
    }


def _agent_intent_adapter(settings: AppSettings) -> AgentIntentAdapter | None:
    if not settings.agent_openai_enabled or settings.openai_api_key is None:
        return None
    return OpenAIResponsesAgentAdapter(
        api_key=settings.openai_api_key,
        model=settings.agent_openai_model,
        timeout_seconds=settings.agent_openai_timeout_seconds,
        base_url=settings.openai_base_url,
    )


def _auth_context(
    household_header: str | None,
    user_header: str | None,
) -> tuple[UUID, UUID] | None:
    if household_header is None or user_header is None:
        return None
    try:
        return UUID(household_header), UUID(user_header)
    except ValueError:
        return None


def _auth_context_missing_response() -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={
            "code": "auth_context_missing",
            "message": "household context is required",
        },
    )


def _coded_error_response(*, status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message},
    )


def _user_context(user_header: str | None) -> UUID | None:
    if user_header is None:
        return None
    try:
        return UUID(user_header)
    except ValueError:
        return None


def _household_context(household_header: str | None) -> UUID | None:
    if household_header is None:
        return None
    try:
        return UUID(household_header)
    except ValueError:
        return None


class _AgentWatchCreator:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_watch(
        self,
        *,
        household_id: UUID,
        user_id: UUID,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str | None,
    ) -> WatchRecord:
        service = WatchService(
            HouseholdWatchRepository(self._session), clock=lambda: datetime.now(UTC)
        )
        return await service.create_watch(
            CreateWatchCommand(
                household_id=household_id,
                owner_user_id=user_id,
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
            )
        )


def _provider_status_response(status: ProviderStatus) -> ProviderStatusResponse:
    return ProviderStatusResponse(
        provider_id=status.provider_id,
        enabled=status.enabled,
        credentials_present=status.credentials_present,
        access_approved=status.access_approved,
        data_kind=status.data_kind.value,
        merge_scope=status.merge_scope.value,
        background_requests_allowed=status.background_requests_allowed,
        user_action_required=status.user_action_required,
        blocked_reasons=list(status.blocked_reasons),
        notes=status.notes,
    )


def _admin_provider_health_response(status: ProviderStatus) -> AdminProviderHealthItemResponse:
    return AdminProviderHealthItemResponse(
        provider_id=status.provider_id,
        enabled=status.enabled,
        credentials_present=status.credentials_present,
        secret_present=status.credentials_present,
        access_approved=status.access_approved,
        data_kind=status.data_kind.value,
        background_requests_allowed=status.background_requests_allowed,
        blocked_reasons=list(status.blocked_reasons),
    )


def _price_source_response(source: PriceSource) -> PriceSourceResponse:
    return PriceSourceResponse(
        id=source.id,
        name=source.name,
        source_type=source.source_type.value,
        price_kind=source.price_kind.value,
        supports_rub=source.supports_rub,
        in_app_booking=source.in_app_booking,
        purchase_flow=source.purchase_flow,
        requires_manual_confirmation=source.requires_manual_confirmation,
        setup_required_ru=source.setup_required_ru,
        notes_ru=source.notes_ru,
    )


def _source_contract_summary_response(
    sources: tuple[SourceReadiness, ...],
) -> SourceContractSummaryResponse:
    return SourceContractSummaryResponse(
        total=len(sources),
        implemented=sum(1 for source in sources if source.stage.value == "implemented"),
        policy_skeleton=sum(1 for source in sources if source.stage.value == "policy_skeleton"),
        contract_only=sum(1 for source in sources if source.stage.value == "contract_only"),
    )


def _source_contract_response(source: SourceReadiness) -> SourceContractResponse:
    return SourceContractResponse(
        source_id=source.source_id,
        display_name=source.display_name,
        stage=source.stage.value,
        adapter_module=source.adapter_module,
        contract_file=source.contract_file,
        terms_url=source.terms_url,
        required_env=list(source.required_env),
        operations=list(source.operations),
        invariants=list(source.invariants),
        notes=source.notes,
        enabled=source.enabled,
        credentials_present=source.credentials_present,
        access_approved=source.access_approved,
        data_kind=source.data_kind,
        merge_scope=source.merge_scope,
        background_requests_allowed=source.background_requests_allowed,
        user_action_required=source.user_action_required,
        blocked_reasons=list(source.blocked_reasons),
    )


def _browser_source_response(source: BrowserSource, *, now: datetime) -> BrowserSourceResponse:
    return BrowserSourceResponse(
        source_id=source.source_id,
        display_name=source.display_name,
        enabled=source.enabled,
        permission_status=source.permission_status(now).value,
        user_action_required=True,
        background_allowed=source.background_allowed,
        supported_routes=list(source.supported_routes),
        current_health=source.current_health,
    )


def _agent_mode_response(settings: AppSettings) -> AgentModeResponse:
    return AgentModeResponse(
        enabled=settings.agent_mode_enabled,
        provider=settings.agent_provider,
        mcp_enabled=settings.agent_mcp_enabled,
        mcp_server_configured=settings.agent_mcp_server is not None,
    )


def _agent_preset_response(preset: AgentPreset) -> AgentPresetResponse:
    return AgentPresetResponse(
        id=preset.id.value,
        title_ru=preset.title_ru,
        description_ru=preset.description_ru,
        required_slots=list(preset.required_slots),
        risk_level=preset.risk_level.value,
    )


def _agent_plan_response(plan: AgentPlan) -> AgentPlanResponse:
    return AgentPlanResponse(
        preset_id=plan.preset_id.value,
        title_ru=plan.title_ru,
        risk_level=plan.risk_level.value,
        missing_slots=list(plan.missing_slots),
        steps=[_agent_plan_step_response(step) for step in plan.steps],
        warnings=list(plan.warnings),
    )


def _agent_plan_step_response(step: AgentPlanStep) -> AgentPlanStepResponse:
    return AgentPlanStepResponse(
        action=step.action,
        title_ru=step.title_ru,
        parameters=step.parameters,
        requires_live_refresh=step.requires_live_refresh,
        explanation_ru=step.explanation_ru,
    )


def _agent_chat_turn_response(response: AgentTurnResponse) -> AgentChatTurnResponse:
    return AgentChatTurnResponse(
        reply_ru=response.reply_ru,
        extracted=response.extracted,
        missing_slots=list(response.missing_slots),
        airport_options={
            key: [_agent_airport_option_response(option) for option in options]
            for key, options in response.airport_options.items()
        },
        actions=[_agent_action_response(action) for action in response.actions],
        audit_events=[_agent_audit_event_response(event) for event in response.audit_events],
        runtime=_agent_runtime_response(response.runtime),
    )


def _agent_runtime_response(runtime: AgentRuntimeInfo) -> AgentRuntimeResponse:
    return AgentRuntimeResponse(
        backend=runtime.backend,
        agentic_loop=runtime.agentic_loop,
        model=runtime.model,
        fallback_backend=runtime.fallback_backend,
        live_calls_allowed=runtime.live_calls_allowed,
        cloudflare_ready=runtime.cloudflare_ready,
    )


def _agent_airport_option_response(option: AirportOption) -> AgentAirportOptionResponse:
    return AgentAirportOptionResponse(
        iata_code=option.iata_code,
        label=option.label,
        name=option.name,
        municipality=option.municipality,
        country_code=option.country_code,
    )


def _agent_action_response(action: AgentAction) -> AgentActionResponse:
    return AgentActionResponse(
        kind=action.kind,
        title_ru=action.title_ru,
        parameters=action.parameters,
        requires_user_action=action.requires_user_action,
        policy_decision=action.policy_decision,
        related_id=action.related_id,
    )


def _agent_audit_event_response(event: AgentAuditEvent) -> AgentAuditEventResponse:
    return AgentAuditEventResponse(
        event_type=event.event_type,
        tool_name=event.tool_name,
        summary=event.summary,
        policy_decision=event.policy_decision,
        related_id=event.related_id,
    )


def _search_response(result: SearchResult) -> SearchResponse:
    priced_offers = [
        _offer_response(
            offer,
            ranking_reasons=result.ranking_reasons.get(offer_ranking_key(offer), ()),
        )
        for offer in result.priced_offers
    ]
    return SearchResponse(
        search_id=result.search_id,
        offers=priced_offers,
        priced_offers=priced_offers,
        provider_isolated_offers=[
            _offer_response(offer, ranking_reasons=()) for offer in result.provider_isolated_offers
        ],
        browser_observed_offers=[
            _browser_observed_offer_response(offer) for offer in result.browser_observed_offers
        ],
        external_links=[_external_search_link_response(link) for link in result.external_links],
        deal_candidates=[
            _deal_candidate_response(candidate) for candidate in result.deal_candidates
        ],
        denied_providers={
            provider_id: ProviderDenialResponse(code=denial.code, message=denial.message)
            for provider_id, denial in result.denied_providers.items()
        },
        warnings=list(result.warnings),
        freshness_summary=_freshness_summary_response(result.freshness_summary),
    )


def _search_intent_from_body(body: SearchRequestBody) -> SearchIntent:
    return SearchIntent(
        origin=body.origin,
        destination=body.destination,
        departure_date=body.departure_date,
        return_date=body.return_date,
        passengers=body.passengers,
        currency=body.currency,
        adults=body.adults,
        children=body.children,
        infants=body.infants,
        trip_type=body.trip_type,
    )


def _live_observation_response(observation: LiveObservation) -> LiveObservationResponse:
    observed_at = observation.completed_at or observation.started_at
    return LiveObservationResponse(
        observation_id=str(observation.observation_id),
        source_id=observation.source_id,
        status=observation.status.value,
        result_scope="live_observed" if observation.offers else "none",
        observed_at=observed_at.isoformat() if observed_at is not None else None,
        offers=[_offer_response(offer, ranking_reasons=()) for offer in observation.offers],
        error_code=observation.error_code.value if observation.error_code is not None else None,
        error_message=observation.error_message,
    )


def _offer_response(offer: FlightOffer, *, ranking_reasons: tuple[str, ...]) -> OfferResponse:
    return OfferResponse(
        provider_id=offer.provider_id,
        provider_offer_id=offer.provider_offer_id,
        origin=offer.origin,
        destination=offer.destination,
        departure_date=offer.departure_date,
        return_date=offer.return_date,
        total_price=_money_response(offer.total_price),
        passengers=offer.passengers,
        observed_at=offer.observed_at.isoformat(),
        freshness=offer.freshness.value,
        requires_live_confirmation=offer.requires_live_confirmation,
        baggage_summary=offer.baggage_summary,
        ranking_reasons=list(ranking_reasons),
    )


def _external_search_link_response(link: ExternalSearchLink) -> ExternalSearchLinkResponse:
    return ExternalSearchLinkResponse(
        kind=link.kind.value,
        source_id=link.source_id,
        source_name=link.source_name,
        url=link.url,
        origin=link.origin,
        destination=link.destination,
        departure_date=link.departure_date,
        return_date=link.return_date,
        passengers=link.passengers,
        adults=link.adults,
        children=link.children,
        infants=link.infants,
        currency=link.currency,
        source_type=link.source_type,
        purchase_flow=link.purchase_flow,
        price_known=link.price_known,
        requires_external_confirmation=link.requires_external_confirmation,
        notes_ru=link.notes_ru,
        warnings=list(link.warnings),
    )


def _browser_observed_offer_response(
    offer: BrowserObservedOffer,
) -> BrowserObservedOfferResponse:
    return BrowserObservedOfferResponse(
        kind=offer.kind.value,
        observation_id=str(offer.observation_id),
        source_id=offer.source_id,
        source_name=offer.source_name,
        provider_offer_id=offer.provider_offer_id,
        origin=offer.origin,
        destination=offer.destination,
        departure_date=offer.departure_date,
        return_date=offer.return_date,
        total_price=_money_response(offer.total_price) if offer.total_price is not None else None,
        passengers=offer.passengers,
        observed_at=offer.observed_at.isoformat(),
        final_url=offer.final_url,
        display_url=offer.display_url,
        freshness=offer.freshness.value,
        confidence=_confidence_value(offer.confidence),
        parser_version=offer.parser_version,
        parser_warnings=list(offer.parser_warnings),
        airline_name=offer.airline_name,
        airline_iata=offer.airline_iata,
        flight_number=offer.flight_number,
        departure_time_local=offer.departure_time_local,
        arrival_time_local=offer.arrival_time_local,
        duration_minutes=offer.duration_minutes,
        stops=offer.stops,
        baggage_summary=offer.baggage_summary,
        seller_name=offer.seller_name,
        requires_external_confirmation=offer.requires_external_confirmation,
    )


def _deal_candidate_response(candidate: DealCandidate) -> DealCandidateResponse:
    return DealCandidateResponse(
        kind=candidate.kind.value,
        source_id=candidate.source_id,
        url=candidate.url,
        title=candidate.title,
        summary_ru=candidate.summary_ru,
        extracted_price=(
            _money_response(candidate.extracted_price)
            if candidate.extracted_price is not None
            else None
        ),
        extracted_origin=candidate.extracted_origin,
        extracted_destination=candidate.extracted_destination,
        extracted_date_window=candidate.extracted_date_window,
        confidence=_confidence_value(candidate.confidence),
        discovered_at=candidate.discovered_at.isoformat(),
        requires_manual_verification=candidate.requires_manual_verification,
    )


def _freshness_summary_response(summary: FreshnessSummary) -> FreshnessSummaryResponse:
    return FreshnessSummaryResponse(
        best_price_source=summary.best_price_source,
        freshest_observation_at=(
            summary.freshest_observation_at.isoformat()
            if summary.freshest_observation_at is not None
            else None
        ),
        needs_external_confirmation=summary.needs_external_confirmation,
    )


def _confidence_value(confidence: Confidence | str) -> str:
    return Confidence(confidence).value


def _money_response(money: Money) -> MoneyResponse:
    return MoneyResponse(
        minor_units=money.minor_units,
        currency=money.currency,
        formatted=str(money),
    )


def _airport_autocomplete_response(
    match: AirportAutocompleteMatch,
) -> AirportAutocompleteItemResponse:
    airport = match.airport
    return AirportAutocompleteItemResponse(
        iata_code=airport.iata_code,
        name=airport.name,
        municipality=airport.municipality,
        country_code=airport.country_code,
        label=match.label,
    )


def _airport_search_match_response(match: AirportSearchMatch) -> AirportAutocompleteItemResponse:
    airport = match.airport
    return AirportAutocompleteItemResponse(
        iata_code=airport.iata_code,
        name=airport.name,
        municipality=airport.municipality,
        country_code=airport.country_code,
        label=match.label,
    )


def _nearby_airport_response(nearby: NearbyAirport) -> NearbyAirportResponse:
    airport = nearby.airport
    return NearbyAirportResponse(
        iata_code=airport.iata_code,
        name=airport.name,
        municipality=airport.municipality,
        country_code=airport.country_code,
        distance_km=nearby.distance_km,
        transfer_note=nearby.transfer_note,
    )


def _date_matrix_response(matrix: DateMatrix) -> DateMatrixResponse:
    return DateMatrixResponse(
        cells=[_date_matrix_cell_response(cell) for cell in matrix.cells],
        provider_calls_required=matrix.provider_calls_required,
        priced=matrix.priced,
    )


def _date_matrix_cell_response(cell: DateMatrixCell) -> DateMatrixCellResponse:
    return DateMatrixCellResponse(
        departure_date=cell.departure_date.isoformat(),
        return_date=cell.return_date.isoformat() if cell.return_date is not None else None,
        stay_days=cell.stay_days,
    )


def _watch_response(watch: WatchRecord) -> WatchResponse:
    return WatchResponse(
        id=str(watch.id),
        household_id=str(watch.household_id),
        owner_user_id=str(watch.owner_user_id),
        origin=watch.origin,
        destination=watch.destination,
        departure_date=watch.departure_date,
        return_date=watch.return_date,
        enabled=watch.enabled,
        created_at=watch.created_at.isoformat(),
    )


def _telegram_update_id(body: dict[str, object]) -> int | None:
    update_id = body.get("update_id")
    return update_id if type(update_id) is int else None


def _telegram_response_status(code: TelegramWebhookDecisionCode) -> tuple[int, str]:
    return {
        TelegramWebhookDecisionCode.ACCEPTED: (202, "accepted"),
        TelegramWebhookDecisionCode.DISABLED: (503, "rejected"),
        TelegramWebhookDecisionCode.DUPLICATE: (200, "ignored"),
        TelegramWebhookDecisionCode.INVALID_UPDATE: (400, "rejected"),
        TelegramWebhookDecisionCode.SECRET_MISMATCH: (403, "rejected"),
    }[code]


app = create_app()
