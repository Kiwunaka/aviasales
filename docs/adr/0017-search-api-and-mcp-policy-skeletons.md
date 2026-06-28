# ADR 0017: Search API and MCP Policy Skeletons

Date: 2026-06-23

## Status

Accepted for the current backend slice.

## Context

The attached plan keeps Aviasales Search API and MCP integration deferred. They must exist as
explicit policy interfaces before any future adapter or tool can be wired, because both categories
can otherwise bypass product invariants:

- Search API results must be provider-isolated;
- every live search requires a real user action grant;
- background execution is forbidden;
- booking links are created only at click time;
- MCP output is untrusted and must pass typed validation;
- MCP cannot receive unrestricted secrets or trigger background live/browser work.

Official Travelpayouts Search API contract notes remain in
`docs/provider-contracts/aviasales-search.md`, verified on 2026-06-23.

## Decision

1. Add `SearchApiPolicyGateway` over the existing `ProviderPolicyGuard`.
2. Model click-time booking as `SearchApiBookingAction` with `preload_allowed=false` for
   Aviasales Search policy.
3. Add `McpResponseValidator` for typed price candidates:
   - money must be integer minor units;
   - currency must be ISO alpha-3;
   - `observed_at` must be timezone-aware;
   - `requires_confirmation` is mandatory.
4. Add `McpPolicyGateway` that denies:
   - unrestricted secrets;
   - scheduler/worker background execution;
   - disabled providers;
   - missing credentials/access;
   - attempts to bypass user action grants.
5. Do not add provider clients, MCP server calls or live traffic in this slice.

## Consequences

- Future Search API adapters must go through the same user-action and isolation checks.
- Future MCP tooling can be evaluated as an interface, not a source of truth.
- The product can expose policy decisions without enabling production Search API or MCP traffic.

## Verification

- `tests/unit/application/test_search_api_policy.py`
- `tests/unit/application/test_mcp_policy.py`
