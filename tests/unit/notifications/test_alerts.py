from __future__ import annotations

from datetime import UTC, datetime, timedelta

from flight_hunter.domain.money import Money
from flight_hunter.notifications.alerts import (
    AlertEvaluationState,
    AlertEvaluator,
    AlertReason,
    PriceObservation,
)

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)


def observation(amount_minor: int, *, observed_at: datetime = NOW) -> PriceObservation:
    return PriceObservation(
        watch_id="watch-1",
        itinerary_fingerprint="route-1",
        observed_at=observed_at,
        price=Money(amount_minor, "PLN"),
    )


def test_twelve_percent_drop_creates_one_price_drop_alert() -> None:
    evaluator = AlertEvaluator(drop_threshold_percent=10, cooldown=timedelta(hours=6))

    result = evaluator.evaluate(
        previous_best=observation(100_000, observed_at=NOW - timedelta(hours=1)),
        current=observation(88_000),
        state=AlertEvaluationState.empty(),
    )

    assert result.alert is not None
    assert result.alert.reason == AlertReason.PRICE_DROP
    assert result.alert.drop_percent == 12
    assert result.alert.dedupe_key == "watch-1:route-1:price_drop:88000"


def test_retry_with_same_price_suppresses_duplicate_alert() -> None:
    evaluator = AlertEvaluator(drop_threshold_percent=10, cooldown=timedelta(hours=6))
    state = AlertEvaluationState.empty()
    first = evaluator.evaluate(
        previous_best=observation(100_000, observed_at=NOW - timedelta(hours=1)),
        current=observation(88_000),
        state=state,
    )

    retry = evaluator.evaluate(
        previous_best=observation(100_000, observed_at=NOW - timedelta(hours=1)),
        current=observation(88_000, observed_at=NOW + timedelta(minutes=5)),
        state=first.state,
    )

    assert first.alert is not None
    assert retry.alert is None
    assert retry.suppressed_reason == "duplicate"


def test_cooldown_suppresses_new_price_bucket_for_same_reason() -> None:
    evaluator = AlertEvaluator(drop_threshold_percent=10, cooldown=timedelta(hours=6))
    first = evaluator.evaluate(
        previous_best=observation(100_000, observed_at=NOW - timedelta(hours=1)),
        current=observation(88_000),
        state=AlertEvaluationState.empty(),
    )

    second = evaluator.evaluate(
        previous_best=observation(100_000, observed_at=NOW - timedelta(hours=1)),
        current=observation(87_000, observed_at=NOW + timedelta(hours=1)),
        state=first.state,
    )

    assert second.alert is None
    assert second.suppressed_reason == "cooldown"


def test_insignificant_change_does_not_alert() -> None:
    evaluator = AlertEvaluator(drop_threshold_percent=10, cooldown=timedelta(hours=6))

    result = evaluator.evaluate(
        previous_best=observation(100_000, observed_at=NOW - timedelta(hours=1)),
        current=observation(95_000),
        state=AlertEvaluationState.empty(),
    )

    assert result.alert is None
    assert result.suppressed_reason == "below_threshold"
