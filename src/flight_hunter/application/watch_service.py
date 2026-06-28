from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from flight_hunter.persistence.repositories import (
    HouseholdWatchRepository,
    NewWatch,
    WatchRecord,
)


@dataclass(frozen=True, slots=True)
class CreateWatchCommand:
    household_id: UUID
    owner_user_id: UUID
    origin: str
    destination: str
    departure_date: str
    return_date: str | None


class WatchService:
    def __init__(
        self,
        repository: HouseholdWatchRepository,
        *,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory

    async def create_watch(self, command: CreateWatchCommand) -> WatchRecord:
        watch = NewWatch(
            id=self._id_factory(),
            household_id=command.household_id,
            owner_user_id=command.owner_user_id,
            origin=command.origin,
            destination=command.destination,
            departure_date=command.departure_date,
            return_date=command.return_date,
            created_at=self._clock(),
        )
        await self._repository.add_watch(watch)
        created = await self._repository.get_watch(command.household_id, watch.id)
        if created is None:
            raise RuntimeError("created watch was not found")
        return created

    async def list_watches(self, household_id: UUID) -> tuple[WatchRecord, ...]:
        return await self._repository.list_watches(household_id)
