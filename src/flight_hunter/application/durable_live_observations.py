from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from flight_hunter.application.live_observations import (
    BrowserSourceCatalog,
    GrantIssueCode,
    GrantIssueDecision,
    GrantSource,
    LiveObservationCreateCode,
    LiveObservationCreateDecision,
    search_intent_fingerprint,
)
from flight_hunter.application.live_refresh import LiveRefreshGate, LiveRefreshState
from flight_hunter.domain.money import Money
from flight_hunter.domain.observation import (
    BrowserSource,
    LiveObservation,
    ObservationStatus,
    PermissionStatus,
)
from flight_hunter.domain.offers import FlightOffer, Freshness, SearchIntent
from flight_hunter.domain.policy import DataKind, ExecutionContext, ProviderPolicy, UserActionGrant
from flight_hunter.persistence.repositories import LiveObservationRepository
from flight_hunter.policy.guard import DenialCode


class DurableLiveObservationService:
    def __init__(
        self,
        *,
        catalog: BrowserSourceCatalog,
        repository: LiveObservationRepository,
        clock: Callable[[], datetime] | None = None,
        grant_ttl: timedelta = timedelta(minutes=5),
        result_ttl: timedelta = timedelta(minutes=15),
    ) -> None:
        self._catalog = catalog
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(UTC))
        self._grant_ttl = grant_ttl
        self._result_ttl = result_ttl
        self._gate = LiveRefreshGate(clock=self._clock)

    async def issue_grant(
        self,
        *,
        user_id: UUID,
        source_id: str,
        search_intent: SearchIntent,
        source: GrantSource,
    ) -> GrantIssueDecision:
        now = self._clock()
        browser_source = self._catalog.get(source_id)
        source_decision = _validate_source(browser_source, now=now)
        if source_decision is not None:
            code, message = source_decision
            return GrantIssueDecision(
                allowed=False,
                code=code,
                message=message,
                grant_token=None,
                expires_at=None,
            )

        grant_id = uuid4()
        expires_at = now + self._grant_ttl
        grant = UserActionGrant(
            id=grant_id,
            user_id=user_id,
            provider_id=source_id,
            action_type="live_observation",
            request_fingerprint=search_intent_fingerprint(search_intent),
            issued_at=now,
            expires_at=expires_at,
            source=source.value,
            consumed_at=None,
        )
        await self._repository.add_grant(grant)
        return GrantIssueDecision(
            allowed=True,
            code=GrantIssueCode.ISSUED,
            message="user action grant issued",
            grant_token=str(grant_id),
            expires_at=expires_at,
        )

    async def create_observation(
        self,
        *,
        user_id: UUID,
        source_id: str,
        search_intent: SearchIntent,
        grant_token: str,
        idempotency_key: str,
        context: ExecutionContext,
    ) -> LiveObservationCreateDecision:
        if (
            existing := await self._repository.get_idempotent_observation_id(
                user_id,
                idempotency_key,
            )
        ) is not None:
            return LiveObservationCreateDecision(
                accepted=True,
                code=LiveObservationCreateCode.QUEUED,
                message="idempotent live observation request already accepted",
                observation_id=existing,
                initial_status=ObservationStatus.QUEUED,
                next_allowed_at=None,
            )

        now = self._clock()
        browser_source = self._catalog.get(source_id)
        source_decision = _validate_source(browser_source, now=now)
        if source_decision is not None:
            code, message = source_decision
            return _deny(code=LiveObservationCreateCode(code.value), message=message)
        if browser_source is None:
            return _deny(
                code=LiveObservationCreateCode.SOURCE_NOT_FOUND,
                message="source not found",
            )

        grant_id = _grant_id_from_token(grant_token)
        grant = (
            await self._repository.get_grant(user_id, grant_id) if grant_id is not None else None
        )
        if grant is None:
            return _deny(
                code=LiveObservationCreateCode.USER_ACTION_GRANT_REQUIRED,
                message="user action grant is required",
            )

        fingerprint = search_intent_fingerprint(search_intent)
        grant_decision = _validate_grant_before_gap(
            grant=grant,
            source_id=source_id,
            request_fingerprint=fingerprint,
            now=now,
        )
        if grant_decision is not None:
            return grant_decision

        policy = _policy_for_source(browser_source, now=now)
        last_refresh_at = await self._repository.last_completed_observation_at(
            user_id=user_id,
            source_id=source_id,
            search_intent_hash=fingerprint,
        )
        decision = self._gate.authorize(
            policy,
            context=context,
            request_fingerprint=fingerprint,
            user_action_grant=grant,
            state=LiveRefreshState(
                provider_id=source_id,
                request_fingerprint=fingerprint,
                last_refresh_at=last_refresh_at,
            ),
        )
        if not decision.allowed:
            return _deny(
                code=_create_code_from_denial(decision.policy_decision.code),
                message=decision.message,
                next_allowed_at=decision.next_allowed_at,
            )

        consumed = await self._repository.consume_grant(grant.id, consumed_at=now)
        if not consumed:
            return _deny(
                code=LiveObservationCreateCode.USER_ACTION_GRANT_CONSUMED,
                message="user action grant consumed",
            )

        observation_id = uuid4()
        queued = LiveObservation(
            observation_id=observation_id,
            grant_id=grant.id,
            user_id=user_id,
            source_id=source_id,
            search_intent_hash=fingerprint,
            status=ObservationStatus.QUEUED,
            created_at=now,
            started_at=None,
            completed_at=None,
            expires_at=now + self._result_ttl,
            offers=(),
            error_code=None,
            error_message=None,
        )
        observation = _run_fake_worker(queued, search_intent, now=now)
        await self._repository.add_observation(observation)
        await self._repository.record_idempotency(
            user_id=user_id,
            idempotency_key=idempotency_key,
            observation_id=observation_id,
            created_at=now,
        )
        return LiveObservationCreateDecision(
            accepted=True,
            code=LiveObservationCreateCode.QUEUED,
            message="live observation queued",
            observation_id=observation_id,
            initial_status=ObservationStatus.QUEUED,
            next_allowed_at=None,
        )

    async def get_observation(
        self,
        *,
        user_id: UUID,
        observation_id: UUID,
    ) -> LiveObservation | None:
        return await self._repository.get_observation(user_id, observation_id)

    def list_sources(self) -> tuple[BrowserSource, ...]:
        return self._catalog.sources()


def _validate_source(
    source: BrowserSource | None,
    *,
    now: datetime,
) -> tuple[GrantIssueCode, str] | None:
    if source is None:
        return GrantIssueCode.SOURCE_NOT_FOUND, "source not found"
    if not source.enabled:
        return GrantIssueCode.SOURCE_DISABLED, "source disabled"
    if source.permission_status(now) != PermissionStatus.ACTIVE:
        return GrantIssueCode.PERMISSION_NOT_VERIFIED, "source permission not verified"
    return None


def _policy_for_source(source: BrowserSource, *, now: datetime) -> ProviderPolicy:
    attestation = source.attestation
    return ProviderPolicy(
        provider_id=source.source_id,
        policy_version="2026-06-23",
        terms_url="https://flight-hunter.local/policies/browser-observer",
        terms_verified_at=attestation.terms_verified_at if attestation is not None else now,
        enabled=source.enabled,
        credentials_present=attestation is not None,
        access_approved=source.permission_status(now) == PermissionStatus.ACTIVE,
        data_kind=DataKind.LIVE,
        background_requests_allowed=False,
        user_action_required=True,
        merge_with_other_sources_allowed=False,
        persist_raw_results_allowed=False,
        persist_normalized_results_allowed=True,
        booking_link_requires_click=True,
        preload_booking_links_allowed=False,
        server_side_only=True,
        real_user_ip_required=False,
        max_requests_per_minute=6,
        max_requests_per_hour_per_user_ip=12,
        cache_ttl_seconds=0,
        result_ttl_seconds=900,
        max_concurrent_requests=1,
        supports_flexible_dates=False,
        supports_nearby_airports=False,
        supports_multi_city=False,
        supports_one_way=True,
        supports_round_trip=True,
        supports_baggage=False,
        supports_fare_rules=False,
        notes="User-action-only fake live observation control plane.",
    )


def _grant_id_from_token(token: str) -> UUID | None:
    try:
        return UUID(token)
    except ValueError:
        return None


def _validate_grant_before_gap(
    *,
    grant: UserActionGrant,
    source_id: str,
    request_fingerprint: str,
    now: datetime,
) -> LiveObservationCreateDecision | None:
    if grant.provider_id != source_id:
        return _deny(
            code=LiveObservationCreateCode.USER_ACTION_GRANT_PROVIDER_MISMATCH,
            message="user action grant provider mismatch",
        )
    if grant.request_fingerprint != request_fingerprint:
        return _deny(
            code=LiveObservationCreateCode.USER_ACTION_GRANT_FINGERPRINT_MISMATCH,
            message="user action grant fingerprint mismatch",
        )
    if grant.consumed_at is not None:
        return _deny(
            code=LiveObservationCreateCode.USER_ACTION_GRANT_CONSUMED,
            message="user action grant consumed",
        )
    if grant.is_expired(now):
        return _deny(
            code=LiveObservationCreateCode.USER_ACTION_GRANT_EXPIRED,
            message="user action grant expired",
        )
    return None


def _run_fake_worker(
    queued: LiveObservation,
    search_intent: SearchIntent,
    *,
    now: datetime,
) -> LiveObservation:
    offer = FlightOffer(
        provider_id=queued.source_id,
        provider_offer_id=f"live-{queued.observation_id}",
        origin=search_intent.origin,
        destination=search_intent.destination,
        departure_date=search_intent.departure_date,
        return_date=search_intent.return_date,
        total_price=Money(minor_units=151200, currency=search_intent.currency),
        passengers=search_intent.passengers,
        observed_at=now,
        freshness=Freshness.LIVE_OBSERVED,
        requires_live_confirmation=True,
        baggage_summary=None,
    )
    return replace(
        queued,
        status=ObservationStatus.SUCCEEDED,
        started_at=now,
        completed_at=now,
        offers=(offer,),
        error_code=None,
        error_message=None,
    )


def _deny(
    *,
    code: LiveObservationCreateCode,
    message: str,
    next_allowed_at: datetime | None = None,
) -> LiveObservationCreateDecision:
    return LiveObservationCreateDecision(
        accepted=False,
        code=code,
        message=message,
        observation_id=None,
        initial_status=None,
        next_allowed_at=next_allowed_at,
    )


def _create_code_from_denial(code: DenialCode) -> LiveObservationCreateCode:
    return {
        DenialCode.BACKGROUND_NOT_ALLOWED: LiveObservationCreateCode.BACKGROUND_NOT_ALLOWED,
        DenialCode.LIVE_REFRESH_TOO_SOON: LiveObservationCreateCode.LIVE_REFRESH_TOO_SOON,
        DenialCode.USER_ACTION_GRANT_CONSUMED: (
            LiveObservationCreateCode.USER_ACTION_GRANT_CONSUMED
        ),
        DenialCode.USER_ACTION_GRANT_EXPIRED: LiveObservationCreateCode.USER_ACTION_GRANT_EXPIRED,
        DenialCode.USER_ACTION_GRANT_FINGERPRINT_MISMATCH: (
            LiveObservationCreateCode.USER_ACTION_GRANT_FINGERPRINT_MISMATCH
        ),
        DenialCode.USER_ACTION_GRANT_PROVIDER_MISMATCH: (
            LiveObservationCreateCode.USER_ACTION_GRANT_PROVIDER_MISMATCH
        ),
        DenialCode.USER_ACTION_GRANT_REQUIRED: (
            LiveObservationCreateCode.USER_ACTION_GRANT_REQUIRED
        ),
    }.get(code, LiveObservationCreateCode.POLICY_DENIED)
