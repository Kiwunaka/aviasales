# ADR 0007: Mergeable Offer Ranking

Date: 2026-06-23

## Status

Accepted.

## Context

Flight Hunter must explain why a result is shown first. It must not treat stale cached prices as equally reliable to live/recent/cached data, and provider-isolated results must not be mixed into the merged ranking.

## Decision

- Rank only mergeable offers inside the application search service.
- Keep provider-isolated offers in a separate response collection.
- Use integer minor units as the base score and add deterministic penalties for freshness, live-confirmation requirement and missing baggage data.
- Return ranking reasons in the API response so UI and Telegram can explain the result without inventing text.

## Consequences

- Ranking is deterministic and testable.
- Cached/stale caveats affect both order and visible explanation.
- Future ranking inputs can be added without changing provider DTOs or making LLM policy decisions.
