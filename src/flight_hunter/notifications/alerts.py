from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from flight_hunter.domain.money import Money
from flight_hunter.domain.policy import require_aware_datetime


class AlertReason(StrEnum):
    PRICE_DROP = "price_drop"


@dataclass(frozen=True, slots=True)
class PriceObservation:
    watch_id: str
    itinerary_fingerprint: str
    observed_at: datetime
    price: Money

    def __post_init__(self) -> None:
        if not self.watch_id:
            raise ValueError("watch_id is required")
        if not self.itinerary_fingerprint:
            raise ValueError("itinerary_fingerprint is required")
        require_aware_datetime(self.observed_at, "observed_at")


@dataclass(frozen=True, slots=True)
class PriceAlert:
    watch_id: str
    itinerary_fingerprint: str
    reason: AlertReason
    observed_at: datetime
    previous_price: Money
    current_price: Money
    drop_percent: int
    dedupe_key: str


@dataclass(frozen=True, slots=True)
class AlertEvaluationState:
    sent_dedupe_keys: frozenset[str]
    last_sent_at_by_bucket: dict[str, datetime]

    @classmethod
    def empty(cls) -> AlertEvaluationState:
        return cls(sent_dedupe_keys=frozenset(), last_sent_at_by_bucket={})

    def record(self, alert: PriceAlert) -> AlertEvaluationState:
        bucket = _cooldown_bucket(
            alert.watch_id,
            alert.itinerary_fingerprint,
            alert.reason,
        )
        next_last_sent = dict(self.last_sent_at_by_bucket)
        next_last_sent[bucket] = alert.observed_at
        return AlertEvaluationState(
            sent_dedupe_keys=self.sent_dedupe_keys | {alert.dedupe_key},
            last_sent_at_by_bucket=next_last_sent,
        )


@dataclass(frozen=True, slots=True)
class AlertEvaluationResult:
    alert: PriceAlert | None
    state: AlertEvaluationState
    suppressed_reason: str | None


class AlertEvaluator:
    def __init__(self, *, drop_threshold_percent: int, cooldown: timedelta) -> None:
        if drop_threshold_percent < 1:
            raise ValueError("drop_threshold_percent must be positive")
        if cooldown < timedelta(0):
            raise ValueError("cooldown cannot be negative")
        self._drop_threshold_percent = drop_threshold_percent
        self._cooldown = cooldown

    def evaluate(
        self,
        *,
        previous_best: PriceObservation,
        current: PriceObservation,
        state: AlertEvaluationState,
    ) -> AlertEvaluationResult:
        self._validate_comparable(previous_best, current)
        drop_percent = self._drop_percent(previous_best.price, current.price)
        if drop_percent < self._drop_threshold_percent:
            return AlertEvaluationResult(
                alert=None,
                state=state,
                suppressed_reason="below_threshold",
            )

        dedupe_key = (
            f"{current.watch_id}:{current.itinerary_fingerprint}:"
            f"{AlertReason.PRICE_DROP.value}:{current.price.minor_units}"
        )
        if dedupe_key in state.sent_dedupe_keys:
            return AlertEvaluationResult(
                alert=None,
                state=state,
                suppressed_reason="duplicate",
            )

        bucket = _cooldown_bucket(
            current.watch_id,
            current.itinerary_fingerprint,
            AlertReason.PRICE_DROP,
        )
        last_sent_at = state.last_sent_at_by_bucket.get(bucket)
        if last_sent_at is not None and current.observed_at - last_sent_at < self._cooldown:
            return AlertEvaluationResult(
                alert=None,
                state=state,
                suppressed_reason="cooldown",
            )

        alert = PriceAlert(
            watch_id=current.watch_id,
            itinerary_fingerprint=current.itinerary_fingerprint,
            reason=AlertReason.PRICE_DROP,
            observed_at=current.observed_at,
            previous_price=previous_best.price,
            current_price=current.price,
            drop_percent=drop_percent,
            dedupe_key=dedupe_key,
        )
        return AlertEvaluationResult(alert=alert, state=state.record(alert), suppressed_reason=None)

    @staticmethod
    def _validate_comparable(previous_best: PriceObservation, current: PriceObservation) -> None:
        if previous_best.watch_id != current.watch_id:
            raise ValueError("watch_id mismatch")
        if previous_best.itinerary_fingerprint != current.itinerary_fingerprint:
            raise ValueError("itinerary_fingerprint mismatch")
        if previous_best.price.currency != current.price.currency:
            raise ValueError("currency mismatch")

    @staticmethod
    def _drop_percent(previous: Money, current: Money) -> int:
        if previous.minor_units <= 0:
            return 0
        if current.minor_units >= previous.minor_units:
            return 0
        return ((previous.minor_units - current.minor_units) * 100) // previous.minor_units


def _cooldown_bucket(
    watch_id: str,
    itinerary_fingerprint: str,
    reason: AlertReason,
) -> str:
    return f"{watch_id}:{itinerary_fingerprint}:{reason.value}"
