# ADR 0018: Live Observation Retention Cleanup

Date: 2026-06-23

## Status

Accepted for the current backend slice.

## Context

Live-observation grants, idempotency keys, normalized offers and observation results are now durable.
The data is intentionally short-lived:

- grants are one-time user-action tokens;
- observation results are live-check evidence that expire quickly;
- idempotency keys should only replay while the related observation is retained;
- raw browser payloads are not stored.

Without an explicit cleanup path, the local/demo database can retain live-check state longer than the
policy TTLs imply.

## Decision

1. Add `LiveObservationRepository.cleanup_expired_live_observation_state(now=...)`.
2. Delete expired observation dependents before their parent rows:
   - `live_observation_offers`;
   - `live_observation_idempotency`;
   - `live_observations`.
3. Delete expired `user_action_grants` as short-lived tokens even when an active observation result
   remains retrievable.
4. Preserve active observation results and their idempotency replay rows until the observation
   `expires_at` is reached.
5. Add `LiveObservationCleanupService.run_once()` as the application entry point for a future worker
   or ops command.
6. Add `flight-hunter-cleanup-live-observations` and `make cleanup-live-observations` as the
   operator-facing command. The command prints only aggregate counts and supports `--dry-run`.

## Consequences

- Retention behavior is deterministic and testable without provider/browser calls.
- Expired grants cannot be reused after cleanup.
- Active live-check results remain visible until their result TTL expires.
- This slice does not schedule cleanup automatically; a worker integration remains pending.
- Operators can run a dry-run cleanup without exposing user IDs, grant tokens or idempotency keys.

## Verification

- `tests/unit/persistence/test_live_observation_repository.py`
- `tests/unit/application/test_live_observation_cleanup.py`
- `tests/unit/ops/test_live_observation_cleanup_cli.py`
