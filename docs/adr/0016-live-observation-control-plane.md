# ADR 0016: Live Observation Control Plane

Date: 2026-06-23

## Status

Accepted for the current backend slice.

## Context

The attached plan separates cached offers from user-triggered live observations. A browser
observer must never become a hidden background scraping system. Before any real source is added,
the product needs a control plane that proves the safety invariants:

- source permission attestation is required;
- a user action grant is one-time and short-lived;
- worker/scheduler contexts cannot start observations;
- repeated client retries are idempotent;
- the returned price is labelled as observed, not guaranteed ticket availability.

## Decision

1. Add `PermissionAttestation`, `BrowserSource`, and `LiveObservation` domain objects.
2. Add `BrowserSourceCatalog` and `LiveObservationService` as an in-memory control plane for this
   slice.
3. Keep browser observation disabled by default through `SCRAPING_OBSERVER_ENABLED=false`.
4. Provide a local `demo_browser` source only for fake-worker validation. It has no external
   network path and no Playwright worker.
5. Add API endpoints:
   - `GET /api/v1/browser-sources`;
   - `POST /api/v1/live-observation-grants`;
   - `POST /api/v1/live-observations`;
   - `GET /api/v1/live-observations/{observation_id}`.
6. Require `Idempotency-Key` for observation creation.
7. Mark fake worker offers as `live_observed` and keep `requires_live_confirmation=true`.

## Consequences

- The UI/Telegram layers can be built against a real control-plane contract before any risky
  source integration exists.
- Retrying the same create request does not create duplicate observations.
- A consumed grant cannot be replayed under a new idempotency key.
- Scheduler/worker code cannot use the control plane as a background live source.
- Real browser workers remain future work and must add per-source fixtures, contract tests,
  network policy, redaction, retention, runbook and explicit permission review.

## Verification

- `tests/unit/domain/test_observation.py`
- `tests/unit/application/test_live_observations.py`
- `tests/unit/api/test_live_observations_api.py`
