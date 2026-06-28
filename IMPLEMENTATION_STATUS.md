# IMPLEMENTATION_STATUS

> Этот файл ведёт coding agent. Статус `done` ставится только после выполнения exit criteria и записи фактических test results.

## External access

| Provider | Adapter | Credentials | Access approved | Enabled | Background allowed | Merge allowed | Last docs verification |
|---|---|---:|---:|---:|---:|---:|---|
| Fake | implemented | n/a | n/a | yes | yes | yes | n/a |
| Aviasales Data | implemented | env/local | token-based | env flag | policy/cached | yes/cached | 2026-06-23 |
| Aviasales Search | policy skeleton only | no | no | no | no | no | 2026-06-23 |
| Skyscanner Indicative | pending | no | no | no | contract | contract | 2026-06-23 |
| Skyscanner Live | pending | no | no | no | no/user action | contract | 2026-06-23 |
| Duffel | pending | no | no | no | contract | contract | 2026-06-23 |

## Mandatory phases

- [ ] Phase 0 - Discovery and ADR
- [ ] Phase 1 - Foundation
- [ ] Phase 2 - Identity/households/audit
- [ ] Phase 3 - Provider Policy Engine
- [ ] Phase 4 - Reference data/PostGIS
- [ ] Phase 5 - Core search/flexible dates/fake provider
- [ ] Phase 6 - Aviasales Data
- [ ] Phase 7 - Canonical offers/ranking/risk/total cost
- [ ] Phase 8 - Itinerary/split/self-transfer/hidden-city gating
- [ ] Phase 9 - Watches/scheduler/history
- [ ] Phase 10 - Price intelligence/deals/alerts
- [ ] Phase 11 - Telegram
- [ ] Phase 12 - Optional live providers
- [ ] Phase 13 - Full UI/PWA/i18n/accessibility
- [ ] Phase 14 - Security/operations/backups/observability
- [ ] Phase 15 - Release readiness

## Acceptance scenarios

- [ ] A Flexible dates
- [ ] B Nearby airports
- [ ] C Split ticket safety
- [ ] D Cached vs live
- [ ] E Aviasales isolation
- [ ] F Tracking
- [ ] G Alert dedupe
- [ ] H Suspected anomaly
- [ ] I Household privacy
- [ ] J Provider failure
- [ ] K No credentials/demo
- [ ] L Telegram security
- [ ] M Booking click gate
- [ ] N Backup/restore
- [ ] O Accessibility/i18n

## Previous slice

- Goal: establish a tested foundation for domain value objects, provider policy enforcement, and deterministic demo provider.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. Create ADR for runtime/tooling and no-live-provider baseline.
  2. Add failing unit tests for Money, policy guard, search planning, and fake provider.
  3. Implement minimal production code that satisfies those tests without external provider calls.
  4. Run `uv run pytest`, `uv run ruff format --check`, `uv run ruff check`, and `uv run mypy`.
- Files/modules:
  - `src/flight_hunter/domain`
  - `src/flight_hunter/policy`
  - `src/flight_hunter/application`
  - `src/flight_hunter/providers`
  - `tests/unit`
- ADR: `docs/adr/0001-python-foundation-and-policy-first.md`
- Tests added:
  - `tests/unit/domain/test_money.py`
  - `tests/unit/policy/test_policy_guard.py`
  - `tests/unit/application/test_search_planner.py`
  - `tests/unit/providers/test_fake_provider.py`
- Docs updated:
  - `README.md`
  - `docs/provider-contracts/aviasales-data.md`
  - `docs/provider-contracts/aviasales-search.md`
- Risks:
  - The full product is not complete in this slice.
  - Local PATH lacks global `ruff`, `mypy`, and `make`; commands are routed through `uv run`.
  - No real provider adapter is implemented yet; Aviasales Data/Search contract notes are documentation and policy inputs only.

## Last verified commands

```text
python --version -> Python 3.12.5
uv --version -> uv 0.9.26
uv python list 3.13 -> cpython-3.13.11 available
uv run pytest tests\unit -> 11 passed, Python 3.14.2
uv run ruff format --check . -> 15 files already formatted
uv run ruff check . -> All checks passed
uv run mypy -> Success: no issues found in 11 source files
pytest --version -> pytest 9.0.2
ruff --version -> not installed globally
mypy --version -> not installed globally
make --version -> not installed globally
git status -> not a git repository
Official Travelpayouts docs checked -> Aviasales Data/Search contract notes recorded
```

## Known external limitations

- No provider credentials are present.
- Aviasales Search, Skyscanner, Duffel live behavior must remain disabled until access is approved and policies are verified.
- The current workspace is not initialized as a git repository.

## No-placeholder audit

- [x] No TODO/pass/NotImplementedError in mandatory production paths for this slice
- [x] No fake response in real provider paths; no real provider paths exist yet
- [x] No live provider calls in CI
- [x] No secrets in repo/client/log fixtures

## Previous slice: backend foundation and demo search

- Goal: add backend foundation endpoints and application-level demo search without real provider calls.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. Add failing tests for provider registry, search service, and FastAPI endpoints.
  2. Implement provider registry with policy-derived status/reasons.
  3. Implement demo search use case using `SearchPlanner` and `FakeFlightProvider`.
  4. Add thin FastAPI delivery adapter for `/healthz`, `/api/v1/providers`, and `/api/v1/searches`.
  5. Run tests, lint, typecheck, and update this file.
- Files/modules:
  - `src/flight_hunter/application/provider_registry.py`
  - `src/flight_hunter/application/search_service.py`
  - `src/flight_hunter/api`
  - `tests/unit/application`
  - `tests/unit/api`
- ADR: `docs/adr/0002-backend-foundation-demo-search.md`
- Tests to add:
  - `tests/unit/application/test_provider_registry.py`
  - `tests/unit/application/test_search_service.py`
  - `tests/unit/api/test_api_app.py`
- Risks:
  - This is still an in-process demo path; persistence, auth, audit, and worker scheduling remain pending.
- Verification:
  - `uv run pytest tests\unit` -> 18 passed
  - `uv run ruff format --check .` -> 22 files already formatted
  - `uv run ruff check .` -> All checks passed
  - `uv run mypy` -> Success: no issues found in 15 source files

## Previous slice: airport autocomplete and nearby demo

- Goal: add airport autocomplete and nearby airport calculation with deterministic demo data.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. Add failing tests for airport distance calculation, autocomplete, nearby service, and API endpoints.
  2. Implement pure geo domain objects and distance calculation.
  3. Implement in-memory demo airport repository and application service.
  4. Add thin FastAPI endpoints for `/api/v1/airports/autocomplete` and `/api/v1/airports/nearby`.
  5. Run tests, lint, typecheck, and update this file.
- Files/modules:
  - `src/flight_hunter/geo`
  - `src/flight_hunter/application/airport_service.py`
  - `src/flight_hunter/api/app.py`
  - `tests/unit/geo`
  - `tests/unit/application`
  - `tests/unit/api`
- ADR: `docs/adr/0003-airport-demo-reference-data.md`
- Tests to add:
  - `tests/unit/geo/test_airports.py`
  - `tests/unit/application/test_airport_service.py`
  - `tests/unit/api/test_airport_api.py`
- Risks:
  - Demo data is intentionally small; full OurAirports importer, PostGIS storage, and admin overrides remain pending.
- Verification:
  - `uv run pytest tests\unit` -> 24 passed
  - `uv run ruff format --check .` -> 29 files already formatted
  - `uv run ruff check .` -> All checks passed
  - `uv run mypy` -> Success: no issues found in 19 source files

## Previous slice: flexible date matrix planning

- Goal: add flexible date matrix planning without provider calls.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. Add failing tests for round-trip date expansion, stay-length filtering, budget limits, and API serialization.
  2. Implement pure date matrix planner in application layer.
  3. Add thin FastAPI endpoint for matrix planning.
  4. Run tests, lint, typecheck, and update this file.
- Files/modules:
  - `src/flight_hunter/application/date_matrix.py`
  - `src/flight_hunter/api/app.py`
  - `tests/unit/application/test_date_matrix.py`
  - `tests/unit/api/test_date_matrix_api.py`
- ADR: `docs/adr/0004-flexible-date-matrix-planning.md`
- Tests to add:
  - `tests/unit/application/test_date_matrix.py`
  - `tests/unit/api/test_date_matrix_api.py`
- Risks:
  - Matrix planning does not price cells yet; provider-backed cached matrix and heatmap persistence remain pending.
- Verification:
  - `uv run pytest tests\unit` -> 28 passed
  - `uv run ruff format --check .` -> 32 files already formatted
  - `uv run ruff check .` -> All checks passed
  - `uv run mypy` -> Success: no issues found in 20 source files

## Previous slice: alert hysteresis and dedupe

- Goal: add price-drop alert hysteresis and dedupe domain logic.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. Add failing tests for 12% drop alert, duplicate retry suppression, cooldown, and insignificant changes.
  2. Implement price snapshot and alert evaluator without Telegram delivery.
  3. Keep calculations in integer minor units.
  4. Run tests, lint, typecheck, and update this file.
- Files/modules:
  - `src/flight_hunter/notifications/alerts.py`
  - `tests/unit/notifications/test_alerts.py`
- ADR: `docs/adr/0005-alert-hysteresis-and-dedupe.md`
- Tests to add:
  - `tests/unit/notifications/test_alerts.py`
- Risks:
  - This does not include persistence, Telegram transport, quiet hours, or retry queue integration yet.
- Verification:
  - `uv run pytest tests\unit` -> 32 passed
  - `uv run ruff format --check .` -> 35 files already formatted
  - `uv run ruff check .` -> All checks passed
  - `uv run mypy` -> Success: no issues found in 22 source files

## Previous slice: beginner-friendly onboarding

- Goal: make the project understandable for a beginner and state what is needed from the user.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. Rewrite README as a short entry point.
  2. Add a plain Russian start guide.
  3. Add the exact demo API command.
  4. Verify the command starts and `/healthz` responds.
- Files/modules:
  - `README.md`
  - `docs/START_HERE_RU.md`
  - `pyproject.toml`
  - `Makefile`
- ADR:
  - n/a
- Tests to add:
  - n/a
- Risks:
  - This improves onboarding only; web UI is still pending.
- What is needed from the user:
  - Nothing required for current demo development.
  - Later, for real Aviasales Data API: Travelpayouts account, API token, optional marker.
  - Later, for Telegram: bot token from `@BotFather`, bot name, and production webhook URL.
  - Later, for production hosting: domain, server/VPS, owner email, generated app secrets.
- Verification:
  - `uv sync --group dev` -> success
  - `uv run uvicorn flight_hunter.api.app:app --host 127.0.0.1 --port 8000` -> server started
  - `GET /healthz` -> `{"app":"Flight Hunter","status":"ok","external_credentials_required":false}`
  - `uv run pytest tests\unit --quiet` -> 32 passed
  - `uv run ruff format --check .` -> 35 files already formatted
  - `uv run ruff check .` -> All checks passed
  - `uv run mypy` -> Success: no issues found in 22 source files

## Previous slice: Aviasales Data adapter and token wiring

- Goal: Aviasales Data API adapter and safe Travelpayouts token wiring.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. Add policy-gated Aviasales Data client/mapper/adapter.
  2. Add `.env`/environment settings without storing secrets in repo.
  3. Wire optional Aviasales Data provider into search planning.
  4. Update user docs with local token setup.
- Files/modules:
  - `src/flight_hunter/providers/aviasales_data`
  - `src/flight_hunter/config.py`
  - `src/flight_hunter/application/provider_registry.py`
  - `src/flight_hunter/application/search_service.py`
- ADR:
  - `docs/provider-contracts/aviasales-data.md`
- Tests to add:
  - `tests/unit/providers/aviasales_data`
  - `tests/unit/test_config.py`
  - `tests/unit/application/test_provider_registry_env.py`
- Risks:
  - The provided token was not stored in the repository. It must be placed in local `.env` by the operator.
  - No live smoke call was run in automated tests. CI remains fixture/transport-only.
- Verification:
  - `uv run pytest tests\unit --quiet` -> 43 passed
  - `uv run ruff format --check .` -> 45 files already formatted
  - `uv run ruff check .` -> All checks passed
  - `uv run mypy` -> Success: no issues found in 27 source files
  - `uv run uvicorn flight_hunter.api.app:app --host 127.0.0.1 --port 8000` -> server started
  - `GET /healthz` -> `{"app":"Flight Hunter","status":"ok","external_credentials_required":false}`

## Previous slice: persistence history and scheduler foundation

- Goal: persistence/auth/watch scheduler foundation.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add persistence models and migration baseline.
  2. [done] Add household isolation repository tests before implementation.
  3. [done] Add watch snapshot history and scheduler eligibility tests.
  4. [done] Integrate alert evaluator with durable dedupe state.
- Files/modules:
  - `src/flight_hunter/persistence/models.py`
  - `src/flight_hunter/persistence/repositories.py`
  - `migrations/versions/0001_initial.py`
  - `migrations/versions/0002_price_history_and_alert_dedupe.py`
  - `src/flight_hunter/application/watch_scheduler.py`
- ADR:
  - `docs/adr/0006-persistence-history-and-scheduler-foundation.md`
- Tests to add:
  - `tests/unit/persistence/test_household_watch_repository.py`
  - `tests/unit/persistence/test_migration_baseline.py`
  - `tests/unit/persistence/test_price_history_and_alert_dedupe.py`
  - `tests/unit/application/test_watch_scheduler.py`
  - `tests/unit/test_env_example.py`
- Risks:
  - Invitation auth, distributed locks, worker process, and watch API endpoints remain pending.
  - SQLite is used for unit tests; PostgreSQL/PostGIS integration tests remain pending.
- Verification:
  - targeted persistence/scheduler tests -> 9 passed

## Previous slice: mergeable offer ranking

- Goal: rank mergeable offers with visible caveats and keep provider-isolated results separate.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. Add failing domain tests for freshness and caveat penalties.
  2. Integrate ranker into search service for mergeable offers only.
  3. Expose ranking reasons in API response.
  4. Document the ranking decision.
- Files/modules:
  - `src/flight_hunter/domain/ranking.py`
  - `src/flight_hunter/application/search_service.py`
  - `src/flight_hunter/api/app.py`
- ADR:
  - `docs/adr/0007-mergeable-offer-ranking.md`
- Tests to add:
  - `tests/unit/domain/test_offer_ranking.py`
  - `tests/unit/application/test_search_service.py`
  - `tests/unit/api/test_api_app.py`
- Risks:
  - Ranking is intentionally simple; itinerary/risk/total-cost model remains pending.
- Verification:
  - targeted ranking/search/API tests -> 11 passed

## Previous slice: beginner web UI

- Goal: add a beginner-friendly web screen without a separate frontend toolchain.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. Add failing test for `GET /`.
  2. Serve a compact FastAPI HTML/CSS/JS screen.
  3. Reuse provider/search API endpoints.
  4. Verify desktop and mobile browser flows.
- Files/modules:
  - `src/flight_hunter/api/web.py`
  - `src/flight_hunter/api/app.py`
  - `README.md`
  - `docs/START_HERE_RU.md`
- ADR:
  - `docs/adr/0008-fastapi-served-beginner-web-ui.md`
- Tests to add:
  - `tests/unit/api/test_web_ui.py`
- Risks:
  - This is a simple served UI, not the final Next.js/PWA.
- Verification:
  - `uv run pytest tests\unit --quiet` -> 58 passed
  - `uv run ruff format --check .` -> 61 files already formatted
  - `uv run ruff check .` -> All checks passed
  - `uv run mypy` -> Success: no issues found in 33 source files
  - Playwright desktop 1440x960 -> search result rendered, no console/page errors
  - Playwright mobile 390x844 -> search result rendered, no horizontal overflow

## Previous slice: migration command and Alembic async upgrade

- Goal: make migrations executable through the project command interface.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. Add failing Alembic upgrade test against temp SQLite.
  2. Switch Alembic env to async engine.
  3. Add `make migrate` / `make dev` commands.
  4. Prevent generated local DB from entering the repo.
- Files/modules:
  - `migrations/env.py`
  - `alembic.ini`
  - `Makefile`
  - `.gitignore`
  - `README.md`
  - `docs/START_HERE_RU.md`
- ADR:
  - n/a
- Tests to add:
  - `tests/unit/persistence/test_alembic_upgrade.py`
- Risks:
  - PostgreSQL integration test remains pending; current migration smoke test uses SQLite.
- Verification:
  - `uv run pytest tests\unit --quiet` -> 59 passed
  - `uv run ruff format --check .` -> 62 files already formatted
  - `uv run ruff check .` -> All checks passed
  - `uv run mypy` -> Success: no issues found in 33 source files
  - `uv run alembic upgrade head` -> upgraded through `0002_price_history_and_alert_dedupe`

## Previous slice: Telegram webhook security foundation

- Goal: add Telegram webhook secret verification and `update_id` dedupe without real bot delivery.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. Add failing pure handler tests.
  2. Add failing FastAPI webhook tests.
  3. Implement disabled, secret mismatch, accepted and duplicate decisions.
  4. Keep Telegram disabled by default.
- Files/modules:
  - `src/flight_hunter/notifications/telegram.py`
  - `src/flight_hunter/api/app.py`
  - `src/flight_hunter/config.py`
  - `README.md`
- ADR:
  - `docs/adr/0009-telegram-webhook-security-foundation.md`
- Tests to add:
  - `tests/unit/notifications/test_telegram_webhook.py`
  - `tests/unit/api/test_telegram_api.py`
- Risks:
  - Dedupe is in-process for this foundation slice; durable Telegram update storage remains pending.
  - No Telegram message delivery is implemented yet.
- Verification:
  - `uv run pytest tests\unit --quiet` -> 65 passed
  - `uv run ruff format --check .` -> 65 files already formatted
  - `uv run ruff check .` -> All checks passed
  - `uv run mypy` -> Success: no issues found in 34 source files

## Previous slice: Aviasales Data smoke helper

- Goal: add a safe local Travelpayouts credential smoke check.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. Re-check official Travelpayouts docs.
  2. Add failing tests for missing credentials, sanitized success and 429.
  3. Implement `travelpayouts-smoke` without printing secrets/raw payloads.
  4. Document local usage.
- Files/modules:
  - `src/flight_hunter/providers/aviasales_data/smoke.py`
  - `pyproject.toml`
  - `Makefile`
  - `README.md`
  - `docs/START_HERE_RU.md`
  - `docs/provider-contracts/aviasales-data.md`
- ADR:
  - `docs/adr/0010-aviasales-data-smoke-helper.md`
- Tests to add:
  - `tests/unit/providers/aviasales_data/test_smoke.py`
- Risks:
  - No live smoke was run because no local `.env` token is stored by the agent.
  - The user-provided token was not written to repo files.
- Verification:
  - `uv run pytest tests\unit\providers\aviasales_data\test_smoke.py -q` -> 3 passed
  - `uv run travelpayouts-smoke` with no local token -> `credentials_missing`, no network

## Previous slice: Watch API household foundation

- Goal: add persistent watch create/list endpoints with household isolation.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. Add failing API tests for missing auth context and household isolation.
  2. Add `WatchService` over persistence repository.
  3. Add `POST /api/v1/watches` and `GET /api/v1/watches`.
  4. Keep route handlers thin and use temporary household/user headers.
- Files/modules:
  - `src/flight_hunter/application/watch_service.py`
  - `src/flight_hunter/api/app.py`
  - `src/flight_hunter/config.py`
  - `README.md`
- ADR:
  - `docs/adr/0011-watch-api-household-context.md`
- Tests to add:
  - `tests/unit/api/test_watch_api.py`
- Risks:
  - Temporary headers are not final invitation/session auth.
  - UI watch creation flow remains pending.
- Verification:
  - `uv run pytest tests\unit\api\test_watch_api.py -q` -> 2 passed
  - `uv run pytest tests\unit --quiet` -> 70 passed
  - `uv run ruff format --check .` -> 69 files already formatted
  - `uv run ruff check .` -> All checks passed
  - `uv run mypy` -> Success: no issues found in 36 source files

## Previous slice: local SQLite backup and restore

- Goal: add beginner-safe local backup/restore commands for demo SQLite.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. Add failing backup/restore tests.
  2. Implement backup copy with timestamped filename.
  3. Implement restore with previous DB preserved.
  4. Add CLI commands and docs.
- Files/modules:
  - `src/flight_hunter/ops/backup.py`
  - `pyproject.toml`
  - `Makefile`
  - `.gitignore`
  - `README.md`
  - `docs/START_HERE_RU.md`
- ADR:
  - `docs/adr/0012-local-sqlite-backup-restore.md`
- Tests to add:
  - `tests/unit/ops/test_backup_restore.py`
- Risks:
  - This is local SQLite backup/restore; PostgreSQL production backup runbook remains pending.
- Verification:
  - `uv run pytest tests\unit\ops\test_backup_restore.py -q` -> 3 passed
  - `uv run flight-hunter-backup --database .\does-not-exist.db --backup-dir .\backups-test` -> `database_missing`
  - `uv run pytest tests\unit --quiet` -> 73 passed
  - `uv run ruff format --check .` -> 72 files already formatted
  - `uv run ruff check .` -> All checks passed
  - `uv run mypy` -> Success: no issues found in 38 source files

## Previous slice: admin provider health endpoint

- Goal: expose provider health state for future admin UI without leaking secrets.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. Add failing API test with token present.
  2. Return provider policy/credential/access state.
  3. Expose boolean secret presence only.
- Files/modules:
  - `src/flight_hunter/api/app.py`
  - `README.md`
- ADR:
  - `docs/adr/0013-admin-provider-health-endpoint.md`
- Tests to add:
  - `tests/unit/api/test_admin_provider_health_api.py`
- Risks:
  - Quota counters, circuit breaker state, and historical health metrics remain pending.
- Verification:
  - `uv run pytest tests\unit\api\test_admin_provider_health_api.py -q` -> 1 passed
  - `uv run pytest tests\unit --quiet` -> 74 passed
  - `uv run ruff format --check .` -> 73 files already formatted
  - `uv run ruff check .` -> All checks passed
  - `uv run mypy` -> Success: no issues found in 38 source files

## Previous slice: agent presets, live refresh gap, price source catalog

- Goal: add a beginner-friendly agent preset layer, a 10-minute live refresh gap,
  and a RUB-first click-out price source model.
- Plan:
  1. [done] Add failing tests for live refresh cooldown and user-action policy.
  2. [done] Add failing tests for agent presets and API responses.
  3. [done] Implement deterministic presets without external LLM/MCP dependency.
  4. [done] Add live refresh gate with default 600-second gap.
  5. [done] Add price source catalog for external purchase flows.
  6. [done] Add scraping observer policy guard for future risky adapters.
  7. [done] Run full quality gate.
- Files/modules:
  - `src/flight_hunter/application/live_refresh.py`
  - `src/flight_hunter/agent/presets.py`
  - `src/flight_hunter/api/app.py`
  - `src/flight_hunter/config.py`
  - `src/flight_hunter/application/price_sources.py`
  - `src/flight_hunter/application/scraping_policy.py`
- ADR:
  - `docs/adr/0014-agent-presets-and-live-refresh-gap.md`
  - `docs/adr/0015-rub-clickout-price-observer.md`
- Tests to add:
  - `tests/unit/application/test_live_refresh.py`
  - `tests/unit/agent/test_presets.py`
  - `tests/unit/api/test_agent_api.py`
  - `tests/unit/application/test_price_sources.py`
  - `tests/unit/api/test_price_sources_api.py`
  - `tests/unit/application/test_scraping_policy.py`
- Risks:
  - Agent mode is deterministic presets only; no external Codex/MCP worker is connected yet.
  - Live provider adapters remain disabled until official access and contract flags are verified.
  - Direct scraping of aggregator/airline pages remains feature-flagged and denied unless
    source permission is documented.
- Verification:
  - `uv run pytest tests/unit --quiet` -> 96 passed
  - `uv run ruff format --check .` -> 84 files already formatted
  - `uv run ruff check .` -> All checks passed
  - `uv run mypy` -> Success: no issues found in 43 source files
  - `rg` exact user-provided Travelpayouts token -> not found in repo files

## Previous slice: live observation control plane and fake worker

- Goal: implement the user-action-only live observation control plane from
  `mega_plan_flight_search.md` without real browser scraping or live provider calls.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add failing domain tests for permission attestation and typed observation states.
  2. [done] Add failing application tests for one-time grants, idempotent observation creation,
     policy denial, and no worker/scheduler background execution.
  3. [done] Add failing API tests for `/api/v1/browser-sources`,
     `/api/v1/live-observation-grants`, `POST /api/v1/live-observations`, and
     `GET /api/v1/live-observations/{observation_id}`.
  4. [done] Implement an in-memory control plane and fake worker with no external network.
  5. [done] Update ADR/docs and run the quality gate.
- Files/modules:
  - `src/flight_hunter/domain/observation.py`
  - `src/flight_hunter/application/live_observations.py`
  - `src/flight_hunter/api/app.py`
  - `docs/provider-contracts/demo-browser-observer.md`
  - `README.md`
- ADR:
  - `docs/adr/0016-live-observation-control-plane.md`
- Tests to add:
  - `tests/unit/domain/test_observation.py`
  - `tests/unit/application/test_live_observations.py`
  - `tests/unit/api/test_live_observations_api.py`
- Risks:
  - This slice intentionally does not add a real Playwright/browser worker.
  - Browser observation remains disabled by default and can only run against the fake worker
    when explicitly enabled for the local demo.
  - Live observed prices still require manual confirmation before purchase.
- Verification:
  - RED: `uv run pytest tests\unit\domain\test_observation.py tests\unit\application\test_live_observations.py tests\unit\api\test_live_observations_api.py -q` -> failed with missing modules.
  - GREEN targeted: same command -> 12 passed.
  - `uv run pytest tests\unit --quiet` -> 108 passed.
  - `uv run ruff format --check .` -> 89 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 45 source files.
  - `uv run alembic upgrade head` -> upgraded local SQLite through `0002_price_history_and_alert_dedupe`.
  - No live provider calls were made.

## Previous slice: Search API and MCP policy skeletons

- Goal: add disabled-by-default policy interfaces for Aviasales Search-style live APIs and
  optional MCP tool output without production traffic or MCP as a source of truth.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add failing tests for Search API provider isolation, user-action-only execution,
     click-time booking action and no background calls.
  2. [done] Add failing tests for MCP output typed validation and policy gateway denial.
  3. [done] Implement application skeletons without provider clients or external calls.
  4. [done] Update ADR/docs and run the quality gate.
- Files/modules:
  - `src/flight_hunter/application/search_api_policy.py`
  - `src/flight_hunter/application/mcp_policy.py`
  - `README.md`
- ADR:
  - `docs/adr/0017-search-api-and-mcp-policy-skeletons.md`
- Tests to add:
  - `tests/unit/application/test_search_api_policy.py`
  - `tests/unit/application/test_mcp_policy.py`
- Risks:
  - Aviasales Search remains disabled until confirmed access and current contract review.
  - MCP integration remains a policy/validation skeleton; no MCP server is called.
- Verification:
  - RED: `uv run pytest tests\unit\application\test_search_api_policy.py tests\unit\application\test_mcp_policy.py -q` -> failed with missing modules.
  - GREEN targeted: same command -> 7 passed.
  - `uv run pytest tests\unit --quiet` -> 115 passed.
  - `uv run ruff format --check .` -> 93 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 47 source files.
  - No provider clients, MCP server calls, or live external calls were added.

## Previous slice: Web UI live-check demo flow

- Goal: activate the local fake live-observer demo and expose the user-click live-check flow in
  the beginner web UI without enabling real browser scraping or provider live calls.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add failing UI tests for live-check endpoints, button copy and no leaked grant token.
  2. [done] Add browser-source test isolation so local `.env` activation does not change
     disabled-by-default policy expectations.
  3. [done] Implement UI JavaScript flow:
     search result -> explicit live check button -> grant -> idempotent observation -> result.
  4. [done] Update docs/status and run the quality gate.
- Files/modules:
  - `.env` (local ignored demo activation, no secrets)
  - `src/flight_hunter/api/web.py`
  - `tests/unit/api/test_web_ui.py`
  - `tests/unit/api/test_live_observations_api.py`
- Risks:
  - This is still the simple FastAPI-served beginner UI, not the final Next.js/PWA.
  - The live check uses `demo_browser` fake worker only.
  - Real browser/source integrations remain disabled until per-source permission and contracts.
- Verification:
  - RED: `uv run pytest tests\unit\api\test_web_ui.py tests\unit\api\test_live_observations_api.py -q`
    -> failed on missing `/api/v1/browser-sources` UI reference.
  - GREEN targeted: same command -> 4 passed.
  - `uv run pytest tests\unit --quiet` -> 115 passed.
  - `uv run ruff format --check .` -> 93 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 47 source files.
  - `uv run alembic upgrade head` -> exit 0.
  - Local `.env` now enables only the fake observer: `SCRAPING_OBSERVER_ENABLED=true`.

## Previous slice: Telegram live-check callback service

- Goal: add a Telegram callback service for cached alerts -> "check live" without storing grant
  tokens, provider secrets or signed URLs in callback data.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add failing tests for safe callback data, callback idempotency and live observation
     creation through `telegram_callback` grants.
  2. [done] Implement application service over `LiveObservationService`.
  3. [done] Document the slice and run the quality gate.
- Files/modules:
  - `src/flight_hunter/application/telegram_live_check.py`
  - `tests/unit/application/test_telegram_live_check.py`
- Risks:
  - This slice does not yet implement durable Telegram account linking.
  - Webhook delivery still returns local API status only; actual Telegram message sending remains pending.
- Verification:
  - RED: `uv run pytest tests\unit\application\test_telegram_live_check.py -q` -> failed with missing module.
  - GREEN targeted: same command -> 3 passed.
  - `uv run pytest tests\unit --quiet` -> 118 passed.
  - `uv run ruff format --check .` -> 95 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 48 source files.
  - `uv run alembic upgrade head` -> exit 0.

## Previous slice: Live observation persistence foundation

- Goal: add durable schema/repository foundation for live observation grants and normalized live
  observation results.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add failing persistence tests for user-scoped grants, one-time consume and
     user-scoped observation lookup.
  2. [done] Add Alembic migration for grants, observations and observation offers.
  3. [done] Implement repository mappings without storing raw HTML/screenshots or secrets.
  4. [done] Run quality gate and update status.
- Files/modules:
  - `src/flight_hunter/persistence/models.py`
  - `src/flight_hunter/persistence/repositories.py`
  - `migrations/versions/0003_live_observations.py`
  - `tests/unit/persistence/test_live_observation_repository.py`
- Risks:
  - API still uses in-memory live observation service in this slice.
  - Full durable service wiring and cleanup/retention job remain pending.
- Verification:
  - RED: `uv run pytest tests\unit\persistence\test_live_observation_repository.py tests\unit\persistence\test_alembic_upgrade.py -q`
    -> failed with missing `LiveObservationRepository`.
  - GREEN targeted: same command -> 3 passed.
  - `uv run pytest tests\unit --quiet` -> 120 passed.
  - `uv run ruff format --check .` -> 97 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 48 source files.
  - `uv run alembic upgrade head` -> upgraded through `0003_live_observations`.

## Previous slice: Durable live-observation API wiring

- Goal: wire live-observation API endpoints to SQL-backed grant/observation/idempotency storage
  instead of process-local memory.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add failing API tests proving observation result and idempotency survive a new app
     instance using the same database.
  2. [done] Add durable idempotency table and repository helpers.
  3. [done] Implement async durable live-observation service over the repository.
  4. [done] Wire API endpoints through per-request DB sessions.
  5. [done] Run quality gate and update status.
- Files/modules:
  - `src/flight_hunter/application/durable_live_observations.py`
  - `src/flight_hunter/api/app.py`
  - `src/flight_hunter/persistence/models.py`
  - `src/flight_hunter/persistence/repositories.py`
  - `migrations/versions/0004_live_observation_idempotency.py`
  - `tests/unit/api/test_live_observations_api.py`
- Risks:
  - Cleanup/retention job remains pending.
  - The fake worker is still synchronous inside request handling for the demo flow.
- Verification:
  - RED: `uv run pytest tests\unit\api\test_live_observations_api.py -q` -> failed with
    persisted observation lookup returning 404 after new app instance.
  - GREEN targeted: same command -> 4 passed.
  - `uv run pytest tests\unit --quiet` -> 121 passed.
  - `uv run ruff format --check .` -> 99 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 49 source files.
  - `uv run alembic upgrade head` -> upgraded through `0004_live_observation_idempotency`.

## Previous slice: Live observation retention cleanup

- Goal: add a safe cleanup path for expired live-observation grants/results/idempotency so local
  demo state does not retain short-lived live-check data indefinitely.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add failing persistence/application tests for expired cleanup and active-result
     preservation.
  2. [done] Implement repository cleanup helpers that remove dependent rows in a safe order.
  3. [done] Add a thin application service for future worker/ops invocation.
  4. [done] Update ADR/docs and run the quality gate.
- Files/modules:
  - `src/flight_hunter/application/live_observation_cleanup.py`
  - `src/flight_hunter/persistence/repositories.py`
  - `tests/unit/application/test_live_observation_cleanup.py`
  - `tests/unit/persistence/test_live_observation_repository.py`
- ADR:
  - `docs/adr/0018-live-observation-retention-cleanup.md`
- Risks:
  - This slice adds a callable cleanup service, not a scheduled production worker yet.
  - No provider/browser calls are made.
- Verification:
  - RED: `uv run pytest tests\unit\persistence\test_live_observation_repository.py tests\unit\application\test_live_observation_cleanup.py -q`
    -> failed with missing `flight_hunter.application.live_observation_cleanup`.
  - GREEN targeted: same command -> 4 passed.
  - `uv run pytest tests\unit --quiet` -> 123 passed.
  - `uv run ruff format --check .` -> 101 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 50 source files.
  - `uv run alembic upgrade head` -> exit 0, current head already applied.

## Previous slice: Live observation cleanup command

- Goal: expose the live-observation retention cleanup through the project command interface for
  local ops without adding background provider/browser execution.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add failing ops tests for dry-run/missing-database/successful cleanup output.
  2. [done] Implement a sanitized CLI over `LiveObservationCleanupService`.
  3. [done] Wire `pyproject.toml`, `Makefile`, and docs.
  4. [done] Run targeted and full quality gate.
- Files/modules:
  - `src/flight_hunter/ops/live_observation_cleanup.py`
  - `tests/unit/ops/test_live_observation_cleanup_cli.py`
  - `pyproject.toml`
  - `Makefile`
  - `README.md`
  - `docs/START_HERE_RU.md`
- ADR:
  - `docs/adr/0018-live-observation-retention-cleanup.md`
- Risks:
  - This remains an operator-triggered command, not an automatic scheduler.
  - The command must not print secrets, raw payloads or PII.
- Verification:
  - RED: `uv run pytest tests\unit\ops\test_live_observation_cleanup_cli.py -q` -> failed
    with missing `flight_hunter.ops.live_observation_cleanup`.
  - GREEN targeted: `uv run pytest tests\unit\ops\test_live_observation_cleanup_cli.py tests\unit\application\test_live_observation_cleanup.py -q` -> 3 passed.
  - Manual CLI missing-db check:
    `uv run flight-hunter-cleanup-live-observations --database-url sqlite+aiosqlite:///./does-not-exist-live-cleanup.db --dry-run`
    -> `database_missing`, no DB file created.
  - `uv run pytest tests\unit --quiet` -> 125 passed.
  - `uv run ruff format --check .` -> 103 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 51 source files.
  - `uv run alembic upgrade head` -> exit 0, current head already applied.

## Previous slice: Durable Telegram update dedupe

- Goal: make Telegram `update_id` dedupe survive app restarts by storing accepted update IDs in
  persistence.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add failing repository/API/migration tests for durable duplicate detection.
  2. [done] Add migration/model/repository for Telegram update IDs.
  3. [done] Wire webhook endpoint to SQL-backed dedupe after secret validation.
  4. [done] Update ADR/docs/status and run quality gate.
- Files/modules:
  - `src/flight_hunter/persistence/models.py`
  - `src/flight_hunter/persistence/repositories.py`
  - `src/flight_hunter/api/app.py`
  - `migrations/versions/0005_telegram_update_dedupe.py`
  - `tests/unit/persistence/test_telegram_update_repository.py`
  - `tests/unit/api/test_telegram_api.py`
- ADR:
  - `docs/adr/0019-durable-telegram-update-dedupe.md`
- Risks:
  - This does not implement Telegram account linking or message delivery yet.
  - Webhook callback actions remain safely unprocessed until linking/ownership checks exist.
- Verification:
  - RED: `uv run pytest tests\unit\persistence\test_telegram_update_repository.py tests\unit\api\test_telegram_api.py tests\unit\persistence\test_alembic_upgrade.py -q`
    -> failed with missing `TelegramUpdateRepository`.
  - GREEN targeted: same command -> 6 passed.
  - `uv run pytest tests\unit --quiet` -> 127 passed.
  - `uv run ruff format --check .` -> 105 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 51 source files.
  - `uv run alembic upgrade head` -> upgraded through `0005_telegram_update_dedupe`.

## Previous slice: Scheduler provider registry fail-closed guard

- Goal: prevent future watch scheduler wiring from registering live/browser/user-action providers,
  even if a provider policy is accidentally misconfigured as background-capable.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add failing scheduler registry tests for cached acceptance and live/user-action
     denial.
  2. [done] Implement `SchedulerProviderRegistry` as a pre-planning allowlist for scheduler-safe
     provider kinds.
  3. [done] Update ADR/docs/status and run quality gate.
- Files/modules:
  - `src/flight_hunter/application/watch_scheduler.py`
  - `tests/unit/application/test_watch_scheduler.py`
- ADR:
  - `docs/adr/0020-scheduler-provider-registry-guard.md`
- Risks:
  - This is a registration guard; a full worker dependency graph is still pending.
- Verification:
  - RED: `uv run pytest tests\unit\application\test_watch_scheduler.py -q` -> failed with
    missing `SchedulerProviderRegistry`.
  - GREEN targeted: same command -> 7 passed.
  - `uv run pytest tests\unit --quiet` -> 130 passed.
  - `uv run ruff format --check .` -> 105 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 51 source files.
  - `uv run alembic upgrade head` -> exit 0, current head already applied.

## Previous slice: SearchIntent passenger mix and trip type

- Goal: extend the domain search intent with explicit passenger mix and trip type while preserving
  the existing `passengers` field used by API/providers.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add failing domain tests for legacy passenger compatibility, explicit
     adults/children/infants validation, and trip-type consistency.
  2. [done] Implement `PassengerMix` and `TripType` in the domain without changing provider
     traffic.
  3. [done] Update docs/status and run quality gate.
- Files/modules:
  - `src/flight_hunter/domain/offers.py`
  - `tests/unit/domain/test_search_intent.py`
- ADR:
  - `docs/adr/0021-search-intent-passenger-mix-and-trip-type.md`
- Risks:
  - API request shape remains backward-compatible in this slice; exposing separate child/infant
    fields in HTTP/UI remains pending.
- Verification:
  - RED: `uv run pytest tests\unit\domain\test_search_intent.py -q` -> failed with missing
    `PassengerMix`.
  - GREEN targeted: same command -> 4 passed.
  - `uv run pytest tests\unit --quiet` -> 134 passed.
  - `uv run ruff format --check .` -> 106 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 51 source files.
  - `uv run alembic upgrade head` -> exit 0, current head already applied.

## Previous slice: Aviasales Data exact-date query planner

- Goal: route Aviasales Data exact-date searches through an explicit planner and fail closed for
  passenger mixes whose pricing basis is not represented by the cached Data API adapter yet.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add failing provider tests for exact one-way/round-trip query planning and
     child/infant passenger mix denial without HTTP calls.
  2. [done] Implement `AviasalesDataQueryPlanner` and wire the adapter through it.
  3. [done] Update provider contract docs/status and run quality gate.
- Files/modules:
  - `src/flight_hunter/providers/aviasales_data/query_planner.py`
  - `src/flight_hunter/providers/aviasales_data/adapter.py`
  - `tests/unit/providers/aviasales_data/test_query_planner.py`
  - `tests/unit/providers/aviasales_data/test_adapter.py`
- ADR:
  - `docs/adr/0022-aviasales-data-exact-date-query-planner.md`
- Docs:
  - `docs/provider-contracts/aviasales-data.md`
- Risks:
  - Broader Data API endpoints such as grouped/latest/popular remain pending.
  - Child/infant pricing is intentionally not estimated from adult cached prices.
- Verification:
  - RED: `uv run pytest tests\unit\providers\aviasales_data\test_query_planner.py tests\unit\providers\aviasales_data\test_adapter.py -q`
    -> failed with missing `flight_hunter.providers.aviasales_data.query_planner`.
  - GREEN targeted: same command -> 6 passed.
  - `uv run pytest tests\unit --quiet` -> 138 passed.
  - `uv run ruff format --check .` -> 108 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 52 source files.
  - `uv run alembic upgrade head` -> exit 0, current head already applied.

## Previous slice: API passenger mix validation

- Goal: expose explicit `adults`/`children`/`infants`/`trip_type` in search request handling while
  keeping the existing `passengers` total backward-compatible.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add failing API/application tests for valid passenger mix propagation and 422 on
     total mismatch.
  2. [done] Add request validation and pass mix fields into `SearchIntent`.
  3. [done] Update docs/status and run quality gate.
- Files/modules:
  - `src/flight_hunter/api/app.py`
  - `src/flight_hunter/application/search_service.py`
  - `tests/unit/api/test_api_app.py`
  - `tests/unit/application/test_search_service.py`
- ADR:
  - `docs/adr/0023-api-passenger-mix-validation.md`
- Risks:
  - The beginner web form still sends only total passengers; richer UI controls remain pending.
- Verification:
  - RED: `uv run pytest tests\unit\api\test_api_app.py tests\unit\application\test_search_service.py -q`
    -> failed because API ignored mismatched mix and `SearchRequest` did not accept `adults`.
  - GREEN targeted: same command -> 11 passed.
  - `uv run pytest tests\unit --quiet` -> 141 passed.
  - `uv run ruff format --check .` -> 108 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 52 source files.
  - `uv run alembic upgrade head` -> exit 0, current head already applied.

## Previous slice: Beginner UI clarity and AI assistant panel

- Goal: replace the confusing narrow demo-looking first screen with a clearer search workbench and
  visible AI assistant panel.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add UI regression checks for visible AI assistant and passenger mix labels.
  2. [done] Redesign the FastAPI-served page using the existing vanilla HTML/CSS/JS stack.
  3. [done] Wire visible AI assistant controls to `/api/v1/agent/presets` and
     `/api/v1/agent/plan`.
  4. [done] Restart the local server and verify the new page is being served.
- Files/modules:
  - `src/flight_hunter/api/web.py`
  - `tests/unit/api/test_web_ui.py`
- Risks:
  - This is still the simple FastAPI-served UI, not the final PWA/Next.js frontend.
  - The AI assistant uses deterministic local presets, not an external LLM chat.
- Verification:
  - Targeted: `uv run pytest tests\unit\api\test_web_ui.py tests\unit\api\test_agent_api.py tests\unit\api\test_api_app.py -q` -> 11 passed.
  - `uv run pytest tests\unit --quiet` -> 141 passed.
  - `uv run ruff format --check .` -> 108 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 52 source files.
  - Local server restarted on `http://127.0.0.1:8001/`; smoke-check found
    `ИИ-помощник`, `Взрослые`, and `/api/v1/agent/plan` in served HTML.

## Current slice: Agent chat and city search

- Goal: turn the visible assistant into a chat-first agent workflow that resolves city names to
  airport choices, runs safe cached search/date/nearby tools, creates watches only from explicit
  user intent, and keeps live checks gated behind user action.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add failing tests for OurAirports import/search, agent chat turns, Codex CLI output
     validation, audit persistence, API responses, and chat-first UI markers.
  2. [done] Add SQLite-compatible airport/import/audit tables, repositories, and an
     `flight-hunter-import-airports` command for local `airports.csv` files.
  3. [done] Implement deterministic `AgentChatService` with typed actions and optional
     `CodexCliAgentAdapter` behind feature flags.
  4. [done] Wire `/api/v1/agent/chat/turn`, `/api/v1/airports/search`, the FastAPI-served UI,
     docs, and command interface.
  5. [done] Run full quality gate and restart the local server.
- Files/modules:
  - `src/flight_hunter/agent/chat.py`
  - `src/flight_hunter/agent/codex_cli.py`
  - `src/flight_hunter/geo/ourairports_importer.py`
  - `src/flight_hunter/persistence/models.py`
  - `src/flight_hunter/persistence/repositories.py`
  - `migrations/versions/0006_airports_and_agent_audit.py`
  - `src/flight_hunter/ops/airport_import.py`
  - `src/flight_hunter/api/app.py`
  - `src/flight_hunter/api/web.py`
- ADR:
  - `docs/adr/0024-agent-chat-city-search-and-codex-cli-bridge.md`
- Risks:
  - Codex CLI must remain optional and sandboxed; it is not a source of prices, routes, provider
    policy, or live availability.
  - Browser/live source selection remains limited to policy/admin-attested sources and cannot
    bypass CAPTCHA, login, geo, anti-bot, proxy, cookie, or access restrictions.
  - OurAirports data is Public Domain but not guaranteed accurate; UI/API must expose import
    provenance and should not imply transfer or airfare savings from geography alone.
- Verification:
  - RED: `uv run pytest tests\unit\geo\test_ourairports_importer.py tests\unit\persistence\test_airport_reference_repository.py tests\unit\agent\test_chat.py tests\unit\agent\test_codex_cli_adapter.py tests\unit\api\test_agent_api.py tests\unit\api\test_web_ui.py tests\unit\ops\test_airport_import_cli.py tests\unit\test_env_example.py -q`
    -> failed with missing `ourairports_importer`, `agent.chat`, `agent.codex_cli`,
    airport repository and airport import command.
  - GREEN targeted: same command -> 18 passed.
  - `uv run pytest tests\unit --quiet` -> 153 passed.
  - `uv run ruff format --check .` -> 118 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 56 source files.
  - `uv run alembic upgrade head` -> upgraded through `0006_airports_and_agent_audit`.
  - Targeted migration/API/UI regression:
    `uv run pytest tests\unit\persistence\test_alembic_upgrade.py tests\unit\api\test_agent_api.py tests\unit\api\test_web_ui.py -q`
    -> 9 passed.
  - Local server restarted on `http://127.0.0.1:8001/` with PID `31204`.
  - Browser smoke: submitted `WAW BCN 2026-10-12 2026-10-19 следи` in the chat UI; the page stayed on
    `/`, rendered airport choices, cached/date/nearby actions, `Watch создан`, and user-action-only
    live check; raw `grant_token` was not displayed.
  - Final gate after browser JS fix:
    - `uv run pytest tests\unit --quiet` -> 153 passed.
    - `uv run ruff format --check .` -> 118 files already formatted.
    - `uv run ruff check .` -> All checks passed.
    - `uv run mypy` -> Success: no issues found in 56 source files.
    - `uv run alembic upgrade head` -> current SQLite migration head verified.

## Current slice: Git publication preparation

- Goal: prepare the existing workspace for safe Git upload without adding product behavior.
- Result: implemented for this repository-hygiene slice. The full product is not complete.
- Plan:
  1. [done] Re-read repository instructions, architecture docs, provider matrix, ADRs, tests,
     migrations, and current status.
  2. [done] Tighten git hygiene so local runtime artifacts and secrets stay out of the
     repository.
  3. [done] Run unit tests, formatter check, lint, typecheck, migration check, and a local
     secret-pattern scan.
  4. [done] Initialize Git, inspect the candidate file set, and create an initial commit if the
     quality gate is green.
- Files/modules:
  - `.gitattributes`
  - `.gitignore`
  - `IMPLEMENTATION_STATUS.md`
- ADR:
  - n/a; this is repository hygiene and release-prep only.
- Risks:
  - No Git remote is configured in this workspace yet.
  - CI is not configured because there is no `.github/workflows` directory in the current tree.
  - Local `.env` and `flight_hunter_dev.db` exist but must remain ignored.
- Verification:
  - `git init -b main` -> initialized local repository on `main`.
  - `git add --dry-run .` -> 161 project files would be added before adding `.gitattributes`;
    local `.env`, SQLite DB, venv,
    caches and runtime directories stayed ignored.
  - `.gitattributes` added to keep repository text files on LF and avoid Windows checkout churn.
  - `git check-ignore -v .env flight_hunter_dev.db .venv .playwright-mcp .run .pytest_cache
    .ruff_cache .mypy_cache .codex-runtime` -> all ignored by `.gitignore`.
  - Broad redacted keyword scan -> 370 documentation/config/code references to secret-related
    words; values were not printed and reviewed as variable names/placeholders/docs.
  - Strict key-format scan (`sk-*`, GitHub tokens, AWS keys, private key blocks, JWT-like tokens)
    -> 0 findings.
  - `uv run pytest tests/unit --quiet` -> 162 passed.
  - `uv run ruff format --check .` -> 120 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 57 source files.
  - `uv run alembic upgrade head` -> current SQLite migration head verified.

## Current slice: OpenAI agent harness and cockpit UI

- Goal: make the chat assistant a policy-aware agent harness with an optional OpenAI Responses
  backend, keep deterministic fallback, and redesign the FastAPI UI as a clearer human-in-the-loop
  agent cockpit.
- Result: implemented for this slice. The full product is not complete.
- Plan:
  1. [done] Add tests for OpenAI Responses payload/schema validation and unsafe output rejection.
  2. [done] Add optional `OpenAIResponsesAgentAdapter` behind `AGENT_OPENAI_ENABLED` and
     `OPENAI_API_KEY` without provider secrets or live/browser execution.
  3. [done] Return agent runtime metadata from `/api/v1/agent/chat/turn`.
  4. [done] Redesign the served UI around `Agent cockpit`, runtime strip, decision rail, airport
     choices, and policy-gated action cards.
  5. [done] Run full quality gate and restart the local server.
- Files/modules:
  - `src/flight_hunter/agent/openai_responses.py`
  - `src/flight_hunter/agent/chat.py`
  - `src/flight_hunter/api/app.py`
  - `src/flight_hunter/api/web.py`
  - `src/flight_hunter/config.py`
  - `tests/unit/agent/test_openai_responses_adapter.py`
  - `tests/unit/api/test_agent_api.py`
  - `tests/unit/api/test_web_ui.py`
  - `.env.example`
- ADR/docs:
  - `docs/adr/0024-agent-chat-city-search-and-codex-cli-bridge.md`
  - `README.md`
  - `docs/START_HERE_RU.md`
- Risks:
  - OpenAI, Codex CLI, and future Cloudflare Agents SDK runtimes remain optional orchestration
    layers only; they are not sources of prices, schedules, provider policy, booking links, or live
    availability.
  - Cloudflare Agents SDK is documented as a future-compatible runtime boundary; this slice keeps
    the production path on FastAPI.
- Verification:
  - Targeted:
    `uv run pytest tests\unit\agent\test_openai_responses_adapter.py tests\unit\agent\test_chat.py tests\unit\api\test_agent_api.py tests\unit\api\test_web_ui.py tests\unit\test_env_example.py -q`
    -> 20 passed.
  - `uv run pytest tests\unit --quiet` -> 162 passed.
  - `uv run ruff format --check .` -> 120 files already formatted.
  - `uv run ruff check .` -> All checks passed.
  - `uv run mypy` -> Success: no issues found in 57 source files.
  - `uv run alembic upgrade head` -> current SQLite migration head verified.
  - Local server restarted on `http://127.0.0.1:8001/`; current listening process PID `5400`.
  - Browser smoke on `http://127.0.0.1:8001/`: submitted
    `Хочу из спб улететь в Шанхай в октябре`; saw `Agent cockpit`,
    `deterministic_harness`, `policy_validated_tool_plan`, `user action only`, airport choices
    `LED`, `PVG`, `SHA`, date clarification for October, and no visible `grant_token`.
  - Follow-up UX fix for `Хочу из спб улететь в Шанхай в октябре`:
    - Added demo/reference support for `LED`, `PVG`, `SHA`, Russian city aliases, and month-only
      `date_hint` handling without guessing an exact flight date.
    - Incomplete chat turns now render `clarify_airport_choice` and `clarify_travel_dates` cards
      instead of a dead-end message.
    - The FastAPI UI clears stale destination/date fields when the agent has not selected them.
    - Provider rows now explain missing real API keys/access as setup state, not a broken search.
    - Browser smoke on `http://127.0.0.1:8001/` with PID `56392`: submitted the phrase above;
      saw `LED`, `PVG`, `SHA`, `Уточнить дату: октябрь`, no `grant_token`, no console errors.
      Screenshot capture was attempted twice but the Browser CDP screenshot command timed out.
    - `uv run pytest tests\unit --quiet` -> 157 passed.
    - `uv run ruff format --check .` -> 118 files already formatted.
    - `uv run ruff check .` -> All checks passed.
    - `uv run mypy` -> Success: no issues found in 56 source files.
    - `uv run alembic upgrade head` -> current SQLite migration head verified.
