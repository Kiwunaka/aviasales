# ADR 0003: Airport demo reference data and distance calculation

Date: 2026-06-23

## Status

Proposed for the current implementation slice.

## Context

Nearby airport search is a core Flight Hunter flow, but the full production implementation needs OurAirports import, PostGIS indexes, admin overrides, and import health checks. Those pieces can be added after a stable domain/application contract exists.

## Decision

- Add pure geo domain objects under `flight_hunter.geo`.
- Use a small deterministic in-memory airport repository for demo mode and API tests.
- Compute distances in code with haversine calculation for now.
- Expose nearby results with a transfer caveat and never claim airfare savings from distance alone.

## Consequences

- Demo mode can exercise autocomplete and nearby airports without external data.
- The repository interface can later be backed by PostgreSQL/PostGIS without changing API behavior.
- This does not complete the production OurAirports importer or spatial index requirements.
