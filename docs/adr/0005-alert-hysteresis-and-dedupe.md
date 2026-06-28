# ADR 0005: Alert hysteresis and dedupe domain logic

Date: 2026-06-23

## Status

Proposed for the current implementation slice.

## Context

Flight Hunter must notify users about meaningful price changes without spamming them. Retries, worker restarts, and repeated snapshots of the same price must not create duplicate alerts.

## Decision

- Add a pure notification-domain alert evaluator.
- Compare integer minor units only.
- Generate deterministic dedupe keys from watch id, itinerary fingerprint, reason, and price bucket.
- Suppress repeated dedupe keys.
- Apply a cooldown for same watch/itinerary/reason after an alert.

## Consequences

- Worker and Telegram delivery can later consume `PriceAlert` objects safely.
- Persistent dedupe storage is still required before production scheduler integration.
