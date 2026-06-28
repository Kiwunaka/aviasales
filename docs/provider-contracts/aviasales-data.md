# Aviasales Data API Contract Notes

Verified: 2026-06-23

Official sources:

- https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API
- https://support.travelpayouts.com/hc/en-us/articles/4402565416594-API-rate-limits

Implementation status: implemented as a policy-gated cached adapter and local smoke helper.

The adapter uses fixture/transport tests and does not make live calls in CI.

`uv run travelpayouts-smoke` can be used manually to verify local credentials. It returns only a sanitized summary and does not print the token, raw payload, booking/search link, or prices.

Policy facts used by Flight Hunter:

- Data API prices are cached from Aviasales user search history, not live availability.
- Cached data can be stored by Aviasales for up to 7 days depending on the query type.
- `/v3/prices_for_dates` is rate-limited by Travelpayouts; the official page lists 600 requests per minute, but Flight Hunter must use its own lower internal limiter.
- A 429 response must be treated as a provider rate-limit signal and never retried aggressively.
- UI, Telegram, and persisted observations must show `observed_at`, freshness, provider source, passengers, and live-confirmation caveats.
- Flight Hunter does not estimate child/infant fares from cached adult-like Data API prices. Until provider-specific passenger pricing is modeled, child/infant passenger mixes fail closed without an HTTP call.

Current Flight Hunter policy:

- Adapter disabled until credentials are configured and `AVIASALES_DATA_ENABLED=true`.
- Data kind: `cached`.
- Background discovery can only be enabled through `ProviderPolicy` and quota guard.
- Merge is allowed only as cached/indicative data; it must never be labelled live.
- API token is sent in `X-Access-Token` and must not appear in query strings, logs, API responses, or client bundles.
- Booking/search links from Data API payloads are not exposed as ready booking URLs by this adapter.
- Exact one-way and round-trip searches are planned through `prices_for_dates`; broader grouped/latest/popular endpoint planning remains pending and must be explicit when added.
