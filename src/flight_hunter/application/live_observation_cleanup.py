from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from flight_hunter.persistence.repositories import (
    LiveObservationCleanupResult,
    LiveObservationRepository,
)


class LiveObservationCleanupService:
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._clock = clock or (lambda: datetime.now(UTC))

    async def run_once(self, *, dry_run: bool = False) -> LiveObservationCleanupResult:
        async with self._session_factory() as session:
            repository = LiveObservationRepository(session)
            result = await repository.cleanup_expired_live_observation_state(now=self._clock())
            if dry_run:
                await session.rollback()
            else:
                await session.commit()
            return result
