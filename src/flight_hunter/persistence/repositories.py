from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, func, insert, or_, select, update
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from flight_hunter.domain.money import Money
from flight_hunter.domain.observation import (
    LiveObservation,
    ObservationErrorCode,
    ObservationStatus,
)
from flight_hunter.domain.offers import FlightOffer, Freshness
from flight_hunter.domain.policy import UserActionGrant, require_aware_datetime
from flight_hunter.geo.airports import (
    Airport,
    AirportImportBatch,
    AirportImportRun,
    AirportType,
)
from flight_hunter.notifications.alerts import AlertEvaluationState, PriceAlert
from flight_hunter.persistence.models import (
    agent_audit_events_table,
    airport_import_runs_table,
    airports_table,
    alert_dedupe_entries_table,
    live_observation_idempotency_table,
    live_observation_offers_table,
    live_observations_table,
    price_snapshots_table,
    telegram_update_dedupe_table,
    user_action_grants_table,
    watches_table,
)


@dataclass(frozen=True, slots=True)
class NewWatch:
    id: UUID
    household_id: UUID
    owner_user_id: UUID
    origin: str
    destination: str
    departure_date: str
    return_date: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class WatchRecord:
    id: UUID
    household_id: UUID
    owner_user_id: UUID
    origin: str
    destination: str
    departure_date: str
    return_date: str | None
    enabled: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class NewPriceSnapshot:
    id: UUID
    household_id: UUID
    watch_id: UUID
    provider_id: str
    itinerary_fingerprint: str
    observed_at: datetime
    price: Money
    freshness: Freshness
    requires_live_confirmation: bool


@dataclass(frozen=True, slots=True)
class PriceSnapshotRecord:
    id: UUID
    household_id: UUID
    watch_id: UUID
    provider_id: str
    itinerary_fingerprint: str
    observed_at: datetime
    price: Money
    freshness: Freshness
    requires_live_confirmation: bool


@dataclass(frozen=True, slots=True)
class LiveObservationCleanupResult:
    grants_deleted: int
    observations_deleted: int
    offers_deleted: int
    idempotency_deleted: int


@dataclass(frozen=True, slots=True)
class AirportSearchMatch:
    airport: Airport
    label: str


@dataclass(frozen=True, slots=True)
class NewAgentAuditEvent:
    id: UUID
    household_id: UUID | None
    user_id: UUID | None
    event_type: str
    tool_name: str
    summary: str
    policy_decision: str
    related_id: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AgentAuditRecord:
    id: UUID
    household_id: UUID | None
    user_id: UUID | None
    event_type: str
    tool_name: str
    summary: str
    policy_decision: str
    related_id: str | None
    created_at: datetime


class AirportReferenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def import_airports(
        self,
        batch: AirportImportBatch,
        *,
        imported_at: datetime,
        source: str = "ourairports",
    ) -> AirportImportRun:
        require_aware_datetime(imported_at, "imported_at")
        for airport in batch.airports:
            values = {
                "iata_code": airport.iata_code,
                "name": airport.name,
                "municipality": airport.municipality,
                "country_code": airport.country_code,
                "latitude": airport.latitude,
                "longitude": airport.longitude,
                "airport_type": airport.airport_type.value,
                "active": airport.active,
                "keywords": ", ".join(airport.keywords),
                "imported_at": imported_at,
            }
            existing = await self._session.execute(
                select(airports_table.c.iata_code)
                .where(airports_table.c.iata_code == airport.iata_code)
                .limit(1)
            )
            if existing.fetchone() is None:
                await self._session.execute(insert(airports_table).values(**values))
            else:
                await self._session.execute(
                    update(airports_table)
                    .where(airports_table.c.iata_code == airport.iata_code)
                    .values(**values)
                )

        import_run = AirportImportRun(
            source=source,
            source_path=str(batch.source_path),
            imported_at=imported_at,
            rows_seen=batch.rows_seen,
            rows_imported=batch.rows_imported,
        )
        await self._session.execute(
            insert(airport_import_runs_table).values(
                id=str(uuid4()),
                source=import_run.source,
                source_path=import_run.source_path,
                imported_at=import_run.imported_at,
                rows_seen=import_run.rows_seen,
                rows_imported=import_run.rows_imported,
            )
        )
        return import_run

    async def search(self, query: str, *, limit: int = 8) -> tuple[AirportSearchMatch, ...]:
        normalized_query = _normalize_airport_query(query)
        if len(normalized_query) < 2:
            return ()

        pattern = f"%{normalized_query}%"
        result = await self._session.execute(
            select(airports_table).where(
                or_(
                    func.lower(airports_table.c.iata_code).like(pattern),
                    func.lower(airports_table.c.name).like(pattern),
                    func.lower(airports_table.c.municipality).like(pattern),
                    func.lower(airports_table.c.keywords).like(pattern),
                )
            )
        )
        matches = tuple(_airport_search_match(row._mapping) for row in result.fetchall())
        return tuple(
            sorted(
                matches,
                key=lambda match: _airport_search_sort_key(match.airport, normalized_query),
            )[:limit]
        )

    async def get(self, iata_code: str) -> Airport | None:
        result = await self._session.execute(
            select(airports_table)
            .where(airports_table.c.iata_code == iata_code.strip().upper())
            .limit(1)
        )
        row = result.fetchone()
        return _airport_from_row(row._mapping) if row is not None else None

    async def latest_import_run(self) -> AirportImportRun | None:
        result = await self._session.execute(
            select(airport_import_runs_table)
            .order_by(airport_import_runs_table.c.imported_at.desc())
            .limit(1)
        )
        row = result.fetchone()
        if row is None:
            return None
        mapping = row._mapping
        return AirportImportRun(
            source=mapping["source"],
            source_path=mapping["source_path"],
            imported_at=mapping["imported_at"],
            rows_seen=mapping["rows_seen"],
            rows_imported=mapping["rows_imported"],
        )


class AgentAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_event(self, event: NewAgentAuditEvent) -> None:
        require_aware_datetime(event.created_at, "created_at")
        await self._session.execute(
            insert(agent_audit_events_table).values(
                id=str(event.id),
                household_id=str(event.household_id) if event.household_id is not None else None,
                user_id=str(event.user_id) if event.user_id is not None else None,
                event_type=event.event_type,
                tool_name=event.tool_name,
                summary=event.summary,
                policy_decision=event.policy_decision,
                related_id=event.related_id,
                created_at=event.created_at,
            )
        )

    async def list_events(self, household_id: UUID) -> tuple[AgentAuditRecord, ...]:
        result = await self._session.execute(
            select(agent_audit_events_table)
            .where(agent_audit_events_table.c.household_id == str(household_id))
            .order_by(agent_audit_events_table.c.created_at, agent_audit_events_table.c.id)
        )
        return tuple(_agent_audit_record(row._mapping) for row in result.fetchall())


class HouseholdWatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_watch(self, watch: NewWatch) -> None:
        await self._session.execute(
            insert(watches_table).values(
                id=str(watch.id),
                household_id=str(watch.household_id),
                owner_user_id=str(watch.owner_user_id),
                origin=watch.origin.upper(),
                destination=watch.destination.upper(),
                departure_date=watch.departure_date,
                return_date=watch.return_date,
                enabled=True,
                created_at=watch.created_at,
            )
        )

    async def list_watches(self, household_id: UUID) -> tuple[WatchRecord, ...]:
        result = await self._session.execute(
            select(watches_table)
            .where(watches_table.c.household_id == str(household_id))
            .order_by(watches_table.c.created_at, watches_table.c.id)
        )
        return tuple(_watch_record(row._mapping) for row in result.fetchall())

    async def get_watch(self, household_id: UUID, watch_id: UUID) -> WatchRecord | None:
        result = await self._session.execute(
            select(watches_table)
            .where(watches_table.c.household_id == str(household_id))
            .where(watches_table.c.id == str(watch_id))
            .limit(1)
        )
        row = result.fetchone()
        return _watch_record(row._mapping) if row is not None else None


class PriceSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_snapshot(self, snapshot: NewPriceSnapshot) -> None:
        await self._session.execute(
            insert(price_snapshots_table).values(
                id=str(snapshot.id),
                household_id=str(snapshot.household_id),
                watch_id=str(snapshot.watch_id),
                provider_id=snapshot.provider_id,
                itinerary_fingerprint=snapshot.itinerary_fingerprint,
                observed_at=snapshot.observed_at,
                amount_minor=snapshot.price.minor_units,
                currency=snapshot.price.currency,
                freshness=snapshot.freshness.value,
                requires_live_confirmation=snapshot.requires_live_confirmation,
            )
        )

    async def list_history(
        self,
        household_id: UUID,
        watch_id: UUID,
    ) -> tuple[PriceSnapshotRecord, ...]:
        result = await self._session.execute(
            select(price_snapshots_table)
            .where(price_snapshots_table.c.household_id == str(household_id))
            .where(price_snapshots_table.c.watch_id == str(watch_id))
            .order_by(price_snapshots_table.c.observed_at, price_snapshots_table.c.id)
        )
        return tuple(_price_snapshot_record(row._mapping) for row in result.fetchall())


class AlertDedupeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load_state(
        self,
        household_id: UUID,
        watch_id: UUID,
    ) -> AlertEvaluationState:
        result = await self._session.execute(
            select(alert_dedupe_entries_table)
            .where(alert_dedupe_entries_table.c.household_id == str(household_id))
            .where(alert_dedupe_entries_table.c.watch_id == str(watch_id))
            .order_by(alert_dedupe_entries_table.c.sent_at)
        )
        sent_dedupe_keys: set[str] = set()
        last_sent_at_by_bucket: dict[str, datetime] = {}
        for row in result.fetchall():
            mapping = row._mapping
            sent_dedupe_keys.add(mapping["dedupe_key"])
            bucket = _alert_bucket(
                watch_id=mapping["watch_id"],
                itinerary_fingerprint=mapping["itinerary_fingerprint"],
                reason=mapping["reason"],
            )
            sent_at = _aware_datetime(mapping["sent_at"])
            previous = last_sent_at_by_bucket.get(bucket)
            if previous is None or sent_at > previous:
                last_sent_at_by_bucket[bucket] = sent_at

        return AlertEvaluationState(
            sent_dedupe_keys=frozenset(sent_dedupe_keys),
            last_sent_at_by_bucket=last_sent_at_by_bucket,
        )

    async def record_alert(self, household_id: UUID, alert: PriceAlert) -> bool:
        existing = await self._session.execute(
            select(alert_dedupe_entries_table.c.dedupe_key)
            .where(alert_dedupe_entries_table.c.dedupe_key == alert.dedupe_key)
            .limit(1)
        )
        if existing.fetchone() is not None:
            return False

        await self._session.execute(
            insert(alert_dedupe_entries_table).values(
                dedupe_key=alert.dedupe_key,
                household_id=str(household_id),
                watch_id=alert.watch_id,
                itinerary_fingerprint=alert.itinerary_fingerprint,
                reason=alert.reason.value,
                sent_at=alert.observed_at,
            )
        )
        return True


class TelegramUpdateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_update(self, *, update_id: int, received_at: datetime) -> bool:
        require_aware_datetime(received_at, "received_at")
        existing = await self._session.execute(
            select(telegram_update_dedupe_table.c.update_id)
            .where(telegram_update_dedupe_table.c.update_id == update_id)
            .limit(1)
        )
        if existing.fetchone() is not None:
            return False

        await self._session.execute(
            insert(telegram_update_dedupe_table).values(
                update_id=update_id,
                received_at=received_at,
            )
        )
        return True


class LiveObservationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_grant(self, grant: UserActionGrant) -> None:
        await self._session.execute(
            insert(user_action_grants_table).values(
                id=str(grant.id),
                user_id=str(grant.user_id),
                provider_id=grant.provider_id,
                action_type=grant.action_type,
                request_fingerprint=grant.request_fingerprint,
                issued_at=grant.issued_at,
                expires_at=grant.expires_at,
                source=grant.source,
                consumed_at=grant.consumed_at,
            )
        )

    async def get_grant(self, user_id: UUID, grant_id: UUID) -> UserActionGrant | None:
        result = await self._session.execute(
            select(user_action_grants_table)
            .where(user_action_grants_table.c.user_id == str(user_id))
            .where(user_action_grants_table.c.id == str(grant_id))
            .limit(1)
        )
        row = result.fetchone()
        return _user_action_grant(row._mapping) if row is not None else None

    async def consume_grant(self, grant_id: UUID, *, consumed_at: datetime) -> bool:
        existing = await self._session.execute(
            select(user_action_grants_table.c.consumed_at)
            .where(user_action_grants_table.c.id == str(grant_id))
            .limit(1)
        )
        row = existing.fetchone()
        if row is None or row._mapping["consumed_at"] is not None:
            return False

        await self._session.execute(
            update(user_action_grants_table)
            .where(user_action_grants_table.c.id == str(grant_id))
            .values(consumed_at=consumed_at)
        )
        return True

    async def add_observation(self, observation: LiveObservation) -> None:
        await self._session.execute(
            insert(live_observations_table).values(
                id=str(observation.observation_id),
                grant_id=str(observation.grant_id),
                user_id=str(observation.user_id),
                source_id=observation.source_id,
                search_intent_hash=observation.search_intent_hash,
                status=observation.status.value,
                created_at=observation.created_at,
                started_at=observation.started_at,
                completed_at=observation.completed_at,
                expires_at=observation.expires_at,
                error_code=(
                    observation.error_code.value if observation.error_code is not None else None
                ),
                error_message=observation.error_message,
            )
        )
        for offer in observation.offers:
            await self._session.execute(
                insert(live_observation_offers_table).values(
                    id=str(uuid4()),
                    observation_id=str(observation.observation_id),
                    provider_id=offer.provider_id,
                    provider_offer_id=offer.provider_offer_id,
                    origin=offer.origin,
                    destination=offer.destination,
                    departure_date=offer.departure_date,
                    return_date=offer.return_date,
                    amount_minor=offer.total_price.minor_units,
                    currency=offer.total_price.currency,
                    passengers=offer.passengers,
                    observed_at=offer.observed_at,
                    freshness=offer.freshness.value,
                    requires_live_confirmation=offer.requires_live_confirmation,
                    baggage_summary=offer.baggage_summary,
                )
            )

    async def get_observation(
        self,
        user_id: UUID,
        observation_id: UUID,
    ) -> LiveObservation | None:
        observation_result = await self._session.execute(
            select(live_observations_table)
            .where(live_observations_table.c.user_id == str(user_id))
            .where(live_observations_table.c.id == str(observation_id))
            .limit(1)
        )
        observation_row = observation_result.fetchone()
        if observation_row is None:
            return None

        offers_result = await self._session.execute(
            select(live_observation_offers_table)
            .where(live_observation_offers_table.c.observation_id == str(observation_id))
            .order_by(live_observation_offers_table.c.id)
        )
        offers = tuple(_live_offer(row._mapping) for row in offers_result.fetchall())
        return _live_observation(observation_row._mapping, offers=offers)

    async def get_idempotent_observation_id(
        self,
        user_id: UUID,
        idempotency_key: str,
    ) -> UUID | None:
        result = await self._session.execute(
            select(live_observation_idempotency_table.c.observation_id)
            .where(live_observation_idempotency_table.c.user_id == str(user_id))
            .where(live_observation_idempotency_table.c.idempotency_key == idempotency_key)
            .limit(1)
        )
        row = result.fetchone()
        return UUID(row._mapping["observation_id"]) if row is not None else None

    async def record_idempotency(
        self,
        *,
        user_id: UUID,
        idempotency_key: str,
        observation_id: UUID,
        created_at: datetime,
    ) -> None:
        await self._session.execute(
            insert(live_observation_idempotency_table).values(
                dedupe_key=_live_observation_dedupe_key(user_id, idempotency_key),
                user_id=str(user_id),
                idempotency_key=idempotency_key,
                observation_id=str(observation_id),
                created_at=created_at,
            )
        )

    async def last_completed_observation_at(
        self,
        *,
        user_id: UUID,
        source_id: str,
        search_intent_hash: str,
    ) -> datetime | None:
        result = await self._session.execute(
            select(live_observations_table.c.completed_at)
            .where(live_observations_table.c.user_id == str(user_id))
            .where(live_observations_table.c.source_id == source_id)
            .where(live_observations_table.c.search_intent_hash == search_intent_hash)
            .where(live_observations_table.c.completed_at.is_not(None))
            .order_by(live_observations_table.c.completed_at.desc())
            .limit(1)
        )
        row = result.fetchone()
        if row is None or row._mapping["completed_at"] is None:
            return None
        return _aware_datetime(row._mapping["completed_at"])

    async def cleanup_expired_live_observation_state(
        self,
        *,
        now: datetime,
    ) -> LiveObservationCleanupResult:
        require_aware_datetime(now, "now")
        expired_observation_ids = await self._expired_observation_ids(now=now)
        offers_deleted = 0
        idempotency_deleted = 0

        if expired_observation_ids:
            offer_ids = await self._offer_ids_for_observations(expired_observation_ids)
            idempotency_keys = await self._idempotency_keys_for_observations(
                expired_observation_ids
            )
            offers_deleted = len(offer_ids)
            idempotency_deleted = len(idempotency_keys)
            if offer_ids:
                await self._session.execute(
                    delete(live_observation_offers_table).where(
                        live_observation_offers_table.c.id.in_(offer_ids)
                    )
                )
            if idempotency_keys:
                await self._session.execute(
                    delete(live_observation_idempotency_table).where(
                        live_observation_idempotency_table.c.dedupe_key.in_(idempotency_keys)
                    )
                )
            await self._session.execute(
                delete(live_observations_table).where(
                    live_observations_table.c.id.in_(expired_observation_ids)
                )
            )

        expired_grant_ids = await self._expired_grant_ids(now=now)
        if expired_grant_ids:
            await self._session.execute(
                delete(user_action_grants_table).where(
                    user_action_grants_table.c.id.in_(expired_grant_ids)
                )
            )

        return LiveObservationCleanupResult(
            grants_deleted=len(expired_grant_ids),
            observations_deleted=len(expired_observation_ids),
            offers_deleted=offers_deleted,
            idempotency_deleted=idempotency_deleted,
        )

    async def _expired_observation_ids(self, *, now: datetime) -> tuple[str, ...]:
        result = await self._session.execute(
            select(live_observations_table.c.id).where(live_observations_table.c.expires_at <= now)
        )
        return tuple(row._mapping["id"] for row in result.fetchall())

    async def _offer_ids_for_observations(
        self,
        observation_ids: tuple[str, ...],
    ) -> tuple[str, ...]:
        result = await self._session.execute(
            select(live_observation_offers_table.c.id).where(
                live_observation_offers_table.c.observation_id.in_(observation_ids)
            )
        )
        return tuple(row._mapping["id"] for row in result.fetchall())

    async def _idempotency_keys_for_observations(
        self,
        observation_ids: tuple[str, ...],
    ) -> tuple[str, ...]:
        result = await self._session.execute(
            select(live_observation_idempotency_table.c.dedupe_key).where(
                live_observation_idempotency_table.c.observation_id.in_(observation_ids)
            )
        )
        return tuple(row._mapping["dedupe_key"] for row in result.fetchall())

    async def _expired_grant_ids(self, *, now: datetime) -> tuple[str, ...]:
        result = await self._session.execute(
            select(user_action_grants_table.c.id).where(
                user_action_grants_table.c.expires_at <= now
            )
        )
        return tuple(row._mapping["id"] for row in result.fetchall())


def _watch_record(row: RowMapping) -> WatchRecord:
    return WatchRecord(
        id=UUID(row["id"]),
        household_id=UUID(row["household_id"]),
        owner_user_id=UUID(row["owner_user_id"]),
        origin=row["origin"],
        destination=row["destination"],
        departure_date=row["departure_date"],
        return_date=row["return_date"],
        enabled=row["enabled"],
        created_at=_aware_datetime(row["created_at"]),
    )


def _airport_search_match(row: RowMapping) -> AirportSearchMatch:
    airport = _airport_from_row(row)
    return AirportSearchMatch(
        airport=airport,
        label=f"{airport.iata_code} - {airport.name}, {airport.municipality}",
    )


def _airport_from_row(row: RowMapping) -> Airport:
    return Airport(
        iata_code=row["iata_code"],
        name=row["name"],
        municipality=row["municipality"],
        country_code=row["country_code"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        airport_type=AirportType(row["airport_type"]),
        active=row["active"],
        keywords=_split_keywords(row["keywords"]),
    )


def _split_keywords(value: str) -> tuple[str, ...]:
    return tuple(keyword.strip() for keyword in value.split(",") if keyword.strip())


def _normalize_airport_query(query: str) -> str:
    normalized = query.strip().lower()
    for prefix, replacement in _CITY_ALIASES.items():
        if normalized.startswith(prefix):
            return replacement
    return normalized


def _airport_search_sort_key(airport: Airport, normalized_query: str) -> tuple[int, int, str]:
    if airport.iata_code.lower().startswith(normalized_query):
        priority = 0
    elif airport.municipality.lower().startswith(normalized_query):
        priority = 1
    elif airport.name.lower().startswith(normalized_query):
        priority = 2
    else:
        priority = 3
    type_priority = 0 if airport.airport_type == AirportType.LARGE_AIRPORT else 1
    return (priority, type_priority, airport.iata_code)


def _agent_audit_record(row: RowMapping) -> AgentAuditRecord:
    return AgentAuditRecord(
        id=UUID(row["id"]),
        household_id=UUID(row["household_id"]) if row["household_id"] is not None else None,
        user_id=UUID(row["user_id"]) if row["user_id"] is not None else None,
        event_type=row["event_type"],
        tool_name=row["tool_name"],
        summary=row["summary"],
        policy_decision=row["policy_decision"],
        related_id=row["related_id"],
        created_at=_aware_datetime(row["created_at"]),
    )


def _price_snapshot_record(row: RowMapping) -> PriceSnapshotRecord:
    return PriceSnapshotRecord(
        id=UUID(row["id"]),
        household_id=UUID(row["household_id"]),
        watch_id=UUID(row["watch_id"]),
        provider_id=row["provider_id"],
        itinerary_fingerprint=row["itinerary_fingerprint"],
        observed_at=_aware_datetime(row["observed_at"]),
        price=Money(row["amount_minor"], row["currency"]),
        freshness=Freshness(row["freshness"]),
        requires_live_confirmation=row["requires_live_confirmation"],
    )


def _user_action_grant(row: RowMapping) -> UserActionGrant:
    return UserActionGrant(
        id=UUID(row["id"]),
        user_id=UUID(row["user_id"]),
        provider_id=row["provider_id"],
        action_type=row["action_type"],
        request_fingerprint=row["request_fingerprint"],
        issued_at=_aware_datetime(row["issued_at"]),
        expires_at=_aware_datetime(row["expires_at"]),
        source=row["source"],
        consumed_at=(
            _aware_datetime(row["consumed_at"]) if row["consumed_at"] is not None else None
        ),
    )


def _live_observation(
    row: RowMapping,
    *,
    offers: tuple[FlightOffer, ...],
) -> LiveObservation:
    return LiveObservation(
        observation_id=UUID(row["id"]),
        grant_id=UUID(row["grant_id"]),
        user_id=UUID(row["user_id"]),
        source_id=row["source_id"],
        search_intent_hash=row["search_intent_hash"],
        status=ObservationStatus(row["status"]),
        created_at=_aware_datetime(row["created_at"]),
        started_at=_aware_datetime(row["started_at"]) if row["started_at"] is not None else None,
        completed_at=(
            _aware_datetime(row["completed_at"]) if row["completed_at"] is not None else None
        ),
        expires_at=_aware_datetime(row["expires_at"]),
        offers=offers,
        error_code=ObservationErrorCode(row["error_code"])
        if row["error_code"] is not None
        else None,
        error_message=row["error_message"],
    )


def _live_offer(row: RowMapping) -> FlightOffer:
    return FlightOffer(
        provider_id=row["provider_id"],
        provider_offer_id=row["provider_offer_id"],
        origin=row["origin"],
        destination=row["destination"],
        departure_date=row["departure_date"],
        return_date=row["return_date"],
        total_price=Money(row["amount_minor"], row["currency"]),
        passengers=row["passengers"],
        observed_at=_aware_datetime(row["observed_at"]),
        freshness=Freshness(row["freshness"]),
        requires_live_confirmation=row["requires_live_confirmation"],
        baggage_summary=row["baggage_summary"],
    )


def _alert_bucket(*, watch_id: str, itinerary_fingerprint: str, reason: str) -> str:
    return f"{watch_id}:{itinerary_fingerprint}:{reason}"


def _live_observation_dedupe_key(user_id: UUID, idempotency_key: str) -> str:
    return f"{user_id}:{idempotency_key}"


def _aware_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value


_CITY_ALIASES: dict[str, str] = {
    "варшав": "warsaw",
    "warszaw": "warsaw",
    "барсел": "barcelona",
    "краков": "krakow",
    "kraków": "krakow",
    "лодз": "lodz",
    "łodz": "lodz",
    "łódź": "lodz",
}
