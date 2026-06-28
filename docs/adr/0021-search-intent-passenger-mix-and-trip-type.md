# ADR 0021: SearchIntent Passenger Mix and Trip Type

Date: 2026-06-23

## Status

Accepted for the current domain slice.

## Context

The mega-plan requires explicit passenger composition and trip type. The current API and providers
already use a flat `passengers` count, so the domain must evolve without breaking existing demo,
provider and live-observation flows.

## Decision

1. Add `PassengerMix(adults, children, infants)` with strict integer validation.
2. Add `TripType.ONE_WAY` and `TripType.ROUND_TRIP`.
3. Keep `SearchIntent.passengers` as the total passenger count for backward compatibility.
4. Infer legacy intents as all-adult passenger mixes.
5. Validate that explicit passenger mix totals match `passengers`.
6. Validate trip type against `return_date`.

## Consequences

- Existing API/provider code continues to use `intent.passengers`.
- Future API/UI/Telegram flows can expose separate adult/child/infant fields safely.
- Pricing still treats all passengers uniformly until provider-specific passenger pricing is added.

## Verification

- `tests/unit/domain/test_search_intent.py`
