# ADR 0010: Aviasales Data Smoke Helper

Date: 2026-06-23

## Status

Accepted.

## Context

Travelpayouts/Aviasales Data credentials should be easy to verify locally, but secrets must not be committed, logged, placed in query strings or exposed in client responses. Aviasales Data is cached data, not live availability.

## Decision

- Add `travelpayouts-smoke` as a local CLI command.
- Read `TRAVELPAYOUTS_API_TOKEN` from environment/`.env`.
- Send the token only through `X-Access-Token`.
- Make one low-limit `prices_for_dates` request and return a sanitized JSON summary.
- Do not print raw provider payload, token, booking/search links or prices.
- Return `credentials_missing` without any network call when the token is absent.

## Consequences

- Operators can verify credentials without exposing secrets.
- CI remains fixture/transport-only.
- This helper does not enable background collection or change provider policy.
