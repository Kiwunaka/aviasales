# ADR 0013: Admin Provider Health Endpoint

Date: 2026-06-23

## Status

Accepted.

## Context

Admins need a provider health/quota screen. The current foundation can expose provider policy state and secret presence without revealing secret values.

## Decision

- Add `GET /api/v1/admin/providers/health`.
- Return provider enabled/access/credential state, data kind, background permission and blocked reasons.
- Return only boolean secret presence; never return secret names or values.
- Defer actual quota counters, circuit-breaker state and historical health metrics to a later operations slice.

## Consequences

- The admin UI can be built against a stable health endpoint.
- Provider secrets remain server-side and unexposed.
