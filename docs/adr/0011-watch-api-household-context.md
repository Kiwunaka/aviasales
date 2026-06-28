# ADR 0011: Watch API Household Context

Date: 2026-06-23

## Status

Accepted.

## Context

Watches must be household-scoped. Full invitation auth is not implemented yet, but the API can already enforce a temporary explicit household/user context and rely on repository filters.

## Decision

- Add `POST /api/v1/watches` and `GET /api/v1/watches`.
- Require `X-Flight-Hunter-Household-Id` and `X-Flight-Hunter-User-Id` headers for this foundation slice.
- Persist watches through `HouseholdWatchRepository`.
- Keep route handlers thin; creation/list orchestration lives in `WatchService`.
- Return stable `auth_context_missing` for missing or invalid context.

## Consequences

- Household isolation is exercised through the API before full auth exists.
- Future invitation/session auth can replace the temporary headers without changing repository isolation.
- The UI still needs a watch workflow in a later slice.
