# ADR 0001: Python foundation and policy-first provider execution

Date: 2026-06-23

## Status

Accepted for the first implementation slice.

## Context

Flight Hunter needs a production-oriented foundation before real provider adapters are added. The repository currently contains the specification pack only. Provider rules require that no HTTP call bypasses a `ProviderPolicy`, and the product must work in demo mode without external credentials.

Version check on 2026-06-23:

- Python.org lists Python 3.14 as the latest feature release and Python 3.13 as an active bugfix line.
- The project specification requires Python 3.13+.
- Local PATH has Python 3.12.5, while `uv run` selected CPython 3.14.2 because the project allows `>=3.13,<3.15`.
- FastAPI documentation supports Pydantic v2, and recommends pinning Pydantic with a `>=2.x,<3.0.0` range.
- Travelpayouts official documentation checked on 2026-06-23 confirms Aviasales Data API cached semantics, Aviasales Search API 50,000+ MAU access, user-action-only search, no automated collection, and click-gated booking links.

## Decision

- Use a `src/` Python package named `flight_hunter`.
- Require Python `>=3.13,<3.15` for the backend package.
- Route local quality commands through `uv run` instead of relying on globally installed `ruff`, `mypy`, or `pytest`.
- Implement pure domain/policy/application code first:
  - `Money` uses integer minor units and ISO currency codes.
  - `ProviderPolicy` and `UserActionGrant` are domain objects.
  - `ProviderPolicyGuard` authorizes every provider operation before an adapter can be called.
  - Search planning separates `MERGEABLE`, `PROVIDER_ISOLATED`, and denied provider work before ranking.
  - `FakeFlightProvider` is explicitly a deterministic demo provider, not a substitute for any real provider.
- Do not add real provider HTTP clients in this slice.
- Record provider contract notes for Aviasales Data and Aviasales Search without enabling live calls.

## Consequences

- Demo and unit tests can run without secrets or network provider access.
- Aviasales Data, Aviasales Search, Skyscanner, and Duffel adapters remain pending and disabled until their contracts are implemented and verified.
- Follow-up slices can add persistence, API, UI, bot, and real adapter contracts on top of the guard.

## References

- https://www.python.org/downloads/
- https://docs.astral.sh/uv/
- https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API
- https://support.travelpayouts.com/hc/en-us/articles/4402565416594-API-rate-limits
- https://support.travelpayouts.com/hc/en-us/articles/30565016140434-Aviasales-Flight-Search-API-real-time-and-multi-city-search
- https://support.travelpayouts.com/hc/en-us/articles/210995808-How-to-get-access-to-the-Aviasales-Search-API
- https://support.travelpayouts.com/hc/en-us/articles/34788165535250-Search-API-usage-rules
