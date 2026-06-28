from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from flight_hunter.domain.money import Money
from flight_hunter.domain.offers import FlightOffer, Freshness, SearchIntent
from flight_hunter.domain.policy import ExecutionContext, ProviderOperation, ProviderPolicy
from flight_hunter.policy.guard import PolicyDecision, ProviderPolicyGuard


class FakeFlightProvider:
    """Deterministic demo provider used only when no real credentials exist."""

    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))
        self.policy = ProviderPolicy.fake(terms_verified_at=self._clock())
        self._guard = ProviderPolicyGuard(clock=self._clock)

    def authorize(
        self,
        *,
        operation: ProviderOperation,
        context: ExecutionContext,
        request_fingerprint: str,
    ) -> PolicyDecision:
        return self._guard.authorize(
            self.policy,
            operation=operation,
            context=context,
            request_fingerprint=request_fingerprint,
        )

    def search(
        self,
        intent: SearchIntent,
        *,
        request_fingerprint: str,
        context: ExecutionContext = ExecutionContext.WEB_USER_ACTION,
    ) -> tuple[FlightOffer, ...]:
        decision = self.authorize(
            operation=ProviderOperation.SEARCH,
            context=context,
            request_fingerprint=request_fingerprint,
        )
        if not decision.allowed:
            return ()

        price_per_passenger = self._price_per_passenger_minor_units(intent)
        total = Money(price_per_passenger * intent.passengers, intent.currency)
        offer_id = (
            f"fake:{intent.origin}:{intent.destination}:"
            f"{intent.departure_date}:{intent.return_date or 'oneway'}:{intent.passengers}"
        )

        return (
            FlightOffer(
                provider_id=self.policy.provider_id,
                provider_offer_id=offer_id,
                origin=intent.origin,
                destination=intent.destination,
                departure_date=intent.departure_date,
                return_date=intent.return_date,
                total_price=total,
                passengers=intent.passengers,
                observed_at=self._clock(),
                freshness=Freshness.CACHED,
                requires_live_confirmation=True,
                baggage_summary=None,
            ),
        )

    @staticmethod
    def _price_per_passenger_minor_units(intent: SearchIntent) -> int:
        route_seed = sum(ord(character) for character in f"{intent.origin}{intent.destination}")
        route_adjustment = (route_seed % 7) * 1_000
        if intent.origin == "WAW" and intent.destination == "BCN":
            return 79_900
        return 69_900 + route_adjustment
