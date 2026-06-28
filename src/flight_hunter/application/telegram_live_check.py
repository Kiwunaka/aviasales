from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from flight_hunter.application.live_observations import (
    GrantSource,
    LiveObservationService,
)
from flight_hunter.domain.observation import LiveObservation
from flight_hunter.domain.offers import FlightOffer, SearchIntent
from flight_hunter.domain.policy import ExecutionContext


@dataclass(frozen=True, slots=True)
class TelegramLiveCheckCallback:
    callback_query_id: str
    telegram_user_id: int
    user_id: UUID
    source_id: str
    search_intent: SearchIntent
    alert_key: str

    def __post_init__(self) -> None:
        if not self.callback_query_id:
            raise ValueError("callback_query_id is required")
        if type(self.telegram_user_id) is not int or self.telegram_user_id < 1:
            raise ValueError("telegram_user_id must be a positive integer")
        if not self.source_id:
            raise ValueError("source_id is required")
        if not self.alert_key:
            raise ValueError("alert_key is required")


@dataclass(frozen=True, slots=True)
class TelegramLiveCheckResult:
    accepted: bool
    code: str
    message: str
    observation_id: UUID | None
    status: str | None
    offer: FlightOffer | None
    idempotent_replay: bool


class TelegramLiveCheckService:
    def __init__(self, *, live_observation_service: LiveObservationService) -> None:
        self._live_observation_service = live_observation_service
        self._callback_observations: dict[str, UUID] = {}

    def handle_callback(self, callback: TelegramLiveCheckCallback) -> TelegramLiveCheckResult:
        idempotency_key = _idempotency_key(callback)
        if (existing := self._callback_observations.get(idempotency_key)) is not None:
            observation = self._live_observation_service.get_observation(
                user_id=callback.user_id,
                observation_id=existing,
            )
            return _result_from_observation(
                accepted=observation is not None,
                code="accepted" if observation is not None else "observation_not_found",
                message="telegram callback replay reused existing observation",
                observation=observation,
                idempotent_replay=True,
            )

        grant = self._live_observation_service.issue_grant(
            user_id=callback.user_id,
            source_id=callback.source_id,
            search_intent=callback.search_intent,
            source=GrantSource.TELEGRAM_CALLBACK,
        )
        if not grant.allowed or grant.grant_token is None:
            return TelegramLiveCheckResult(
                accepted=False,
                code=grant.code.value,
                message=grant.message,
                observation_id=None,
                status=None,
                offer=None,
                idempotent_replay=False,
            )

        created = self._live_observation_service.create_observation(
            user_id=callback.user_id,
            source_id=callback.source_id,
            search_intent=callback.search_intent,
            grant_token=grant.grant_token,
            idempotency_key=idempotency_key,
            context=ExecutionContext.TELEGRAM_CALLBACK,
        )
        if not created.accepted or created.observation_id is None:
            return TelegramLiveCheckResult(
                accepted=False,
                code=created.code.value,
                message=created.message,
                observation_id=None,
                status=None,
                offer=None,
                idempotent_replay=False,
            )

        self._callback_observations[idempotency_key] = created.observation_id
        observation = self._live_observation_service.get_observation(
            user_id=callback.user_id,
            observation_id=created.observation_id,
        )
        return _result_from_observation(
            accepted=observation is not None,
            code="accepted" if observation is not None else "observation_not_found",
            message="telegram live check observation created",
            observation=observation,
            idempotent_replay=False,
        )


def build_live_check_callback_data(*, source_id: str, alert_key: str) -> str:
    if not source_id:
        raise ValueError("source_id is required")
    if not alert_key:
        raise ValueError("alert_key is required")
    return f"live_check:{source_id}:{alert_key}"


def _idempotency_key(callback: TelegramLiveCheckCallback) -> str:
    return f"telegram:{callback.telegram_user_id}:{callback.callback_query_id}"


def _result_from_observation(
    *,
    accepted: bool,
    code: str,
    message: str,
    observation: LiveObservation | None,
    idempotent_replay: bool,
) -> TelegramLiveCheckResult:
    if observation is None:
        return TelegramLiveCheckResult(
            accepted=accepted,
            code=code,
            message=message,
            observation_id=None,
            status=None,
            offer=None,
            idempotent_replay=idempotent_replay,
        )

    live_observation = observation
    return TelegramLiveCheckResult(
        accepted=accepted,
        code=code,
        message=message,
        observation_id=live_observation.observation_id,
        status=live_observation.status.value,
        offer=live_observation.offers[0] if live_observation.offers else None,
        idempotent_replay=idempotent_replay,
    )
