# ADR 0025: Provider Source Contract Catalog

Date: 2026-06-29

## Status

Accepted for the current source-readiness slice.

## Context

The provider layer already has a policy guard and one implemented real adapter, Aviasales Data.
However, the repository can look underdeveloped from GitHub or API inspection because unavailable
sources are represented mostly as policy notes and disabled registry entries. That makes it harder
to see the difference between:

- implemented adapters;
- policy skeletons that intentionally block execution;
- contract-only providers waiting on credentials, access approval and fixture-backed tests;
- reference data sources that are implemented but are not fare providers.

The product must not make disabled live providers look available, but it should expose the source
roadmap and safety invariants in code.

## Decision

1. Add `SourceContractCatalog` in the application layer.
2. Keep `ProviderRegistry` as the runtime policy source for execution decisions.
3. Let the source contract catalog combine:
   - implementation stage;
   - adapter module path when implemented;
   - contract/documentation file;
   - provider terms URL;
   - required environment variables by name only;
   - supported operations;
   - safety invariants;
   - policy-derived enabled/credential/access/background/merge status.
4. Expose `GET /api/v1/source-contracts`.
5. Never expose secret values through the catalog.
6. Mark Aviasales Search as `policy_skeleton` and keep it provider-isolated, user-action-only and
   background-denied.
7. Mark Skyscanner and Duffel as `contract_only` until partnership/contract flags and adapters are
   implemented with fixtures and contract tests.
8. Include OurAirports as an implemented reference-data source, while keeping it separate from fare
   providers.

## Consequences

- GitHub/API readers can see which sources are real, gated or future work without reading every
  policy class.
- The source layer is no longer visually "empty", but unavailable live providers remain honestly
  disabled.
- Provider execution still goes through `ProviderPolicyGuard`; the catalog is explanatory and
  diagnostic, not an authorization bypass.
- Adding a new provider now requires both a policy and a source contract entry.

## Verification

- `tests/unit/application/test_source_contracts.py`
- `tests/unit/api/test_source_contracts_api.py`
