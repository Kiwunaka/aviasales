# ADR 0006: Persistence History And Scheduler Foundation

Date: 2026-06-23

## Status

Accepted.

## Context

Watches, price history, alert dedupe and scheduler decisions must be durable and household-scoped. A retry must not duplicate alerts, and a background worker must never call a provider whose policy forbids background execution.

## Decision

- Use SQLAlchemy async repositories behind application/domain code.
- Keep price snapshots append-only.
- Store alert dedupe entries durably by dedupe key and reconstruct `AlertEvaluationState` from storage.
- Keep scheduler eligibility as deterministic application logic before any worker/provider call.
- Use provider policy guard inside scheduler planning for background checks.
- Add Alembic migrations for every schema change after the baseline.

## Consequences

- The current implementation can be tested with SQLite in unit tests and later run on PostgreSQL/PostGIS.
- Household filters are explicit in repository methods.
- Scheduler decisions are inspectable and can explain blocked providers.
- Invitation auth, distributed locks and worker execution remain separate follow-up slices.
