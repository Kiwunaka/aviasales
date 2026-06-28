# ADR 0022: Aviasales Data Exact-Date Query Planner

Date: 2026-06-24

## Status

Accepted for the current provider slice.

## Context

The mega-plan requires an explicit Data API query planner instead of silent fallback between
Travelpayouts/Aviasales Data endpoints. The current adapter only implements `prices_for_dates`.
After adding passenger mix to `SearchIntent`, the adapter also must avoid inventing child/infant
pricing from cached adult-like prices.

## Decision

1. Add `AviasalesDataQueryPlanner`.
2. Plan exact one-way and round-trip searches through `prices_for_dates`.
3. Mark plans as non-degraded; no broader endpoint fallback is performed in this slice.
4. Fail closed for passenger mixes with children or infants until provider-specific pricing basis is
   modeled.
5. Keep CI on mocked transports only; no live provider calls are added.

## Consequences

- The adapter no longer constructs `prices_for_dates` queries inline.
- Child/infant searches return no Aviasales Data offers rather than misleading totals.
- Grouped/latest/popular endpoint planning remains pending and must be added explicitly.

## Verification

- `tests/unit/providers/aviasales_data/test_query_planner.py`
- `tests/unit/providers/aviasales_data/test_adapter.py`
