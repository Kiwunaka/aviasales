# ADR 0023: API Passenger Mix Validation

Date: 2026-06-24

## Status

Accepted for the current API slice.

## Context

`SearchIntent` now supports explicit adult, child and infant counts, but the public API previously
accepted only a flat `passengers` total. Invalid totals could reach domain construction indirectly
or be ignored by delivery code.

## Decision

1. Keep `passengers` as the required total for backward compatibility.
2. Add optional `adults`, `children`, `infants` and `trip_type` fields to `SearchRequestBody`.
3. Validate `passengers == adults + children + infants` when mix fields are supplied.
4. Validate `trip_type` against `return_date`.
5. Include passenger mix fields in search fingerprints.

## Consequences

- Existing web/API clients that send only `passengers` continue to work.
- Richer clients can send passenger composition safely.
- Invalid passenger totals return a stable FastAPI validation error instead of reaching providers.

## Verification

- `tests/unit/api/test_api_app.py`
- `tests/unit/application/test_search_service.py`
