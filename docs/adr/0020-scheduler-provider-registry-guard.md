# ADR 0020: Scheduler Provider Registry Guard

Date: 2026-06-23

## Status

Accepted for the current scheduler slice.

## Context

The watch scheduler must never call browser observers, live user-action providers or any provider
that requires a real user gesture. The policy guard already denies normal background-disallowed
providers, but future worker wiring needs a fail-closed registration boundary before planning.

## Decision

1. Add `SchedulerProviderRegistry` in the application layer.
2. Accept cached/background-safe providers.
3. Reject:
   - `DataKind.LIVE` providers;
   - providers with `user_action_required=true`;
   - providers with `background_requests_allowed=false`.
4. Keep `WatchSchedulerPlanner` policy checks as a second layer.

## Consequences

- A misconfigured live/browser provider cannot enter the scheduler provider set.
- The scheduler still needs a full worker dependency graph and lock/job execution layer.
- Browser observer execution remains user-action-only.

## Verification

- `tests/unit/application/test_watch_scheduler.py`
