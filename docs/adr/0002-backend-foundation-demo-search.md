# ADR 0002: Backend foundation and demo search delivery

Date: 2026-06-23

## Status

Proposed for the current implementation slice.

## Context

Flight Hunter needs a working backend surface before persistence, web UI, Telegram, and real provider adapters can be attached. The backend must remain usable without external credentials and must show provider policy limitations clearly.

## Decision

- Add a thin FastAPI delivery adapter under `flight_hunter.api`.
- Keep business decisions in application services:
  - provider status is computed by `ProviderRegistry`;
  - demo search orchestration is computed by `DemoSearchService`;
  - FastAPI routes only validate/serialize and call application services.
- Expose:
  - `GET /healthz`;
  - `GET /api/v1/providers`;
  - `POST /api/v1/searches`.
- Use `FakeFlightProvider` as a deterministic demo source only.
- Keep Aviasales Search disabled and provider-isolated by policy.

## Consequences

- A clean install can exercise a real backend demo search without API keys.
- Provider status can explain `credentials_missing`, `access_not_approved`, and `provider_disabled`.
- Persistence, auth, audit, rate limiting, SSE, and worker execution remain follow-up slices.
