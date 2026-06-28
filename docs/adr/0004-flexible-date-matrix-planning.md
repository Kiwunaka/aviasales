# ADR 0004: Flexible date matrix planning without provider calls

Date: 2026-06-23

## Status

Proposed for the current implementation slice.

## Context

Flexible date search must not blindly fan out into live provider calls. For a round trip with +/-3 days, users expect a 7x7-compatible matrix, but provider execution has to be planned separately according to cached/live policy.

## Decision

- Add an application-level `DateMatrixPlanner`.
- Generate unpriced planning cells without calling any provider.
- Cap flexibility to prevent unbounded combinations.
- Record `provider_calls_required=0` for this planning step.
- Apply optional stay-length filters before provider execution.

## Consequences

- The API can show matrix shape and candidate cells before pricing.
- Cached/indicative pricing can later fill cells without changing the planner contract.
- Live refresh remains a separate user-action-gated operation.
