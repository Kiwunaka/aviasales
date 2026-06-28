# IMPLEMENTATION_STATUS

> Этот файл ведёт coding agent. Статус `done` ставится только после выполнения exit criteria и записи фактических test results.

## External access

| Provider | Adapter | Credentials | Access approved | Enabled | Background allowed | Merge allowed | Last docs verification |
|---|---|---:|---:|---:|---:|---:|---|
| Fake | pending | n/a | n/a | yes | yes | yes | n/a |
| Aviasales Data | pending | no | token-based | no | policy | yes/cached | 2026-06-23 |
| Aviasales Search | pending | no | no | no | no | no | 2026-06-23 |
| Skyscanner Indicative | pending | no | no | no | contract | contract | 2026-06-23 |
| Skyscanner Live | pending | no | no | no | no/user action | contract | 2026-06-23 |
| Duffel | pending | no | no | no | contract | contract | 2026-06-23 |

## Mandatory phases

- [ ] Phase 0 — Discovery and ADR
- [ ] Phase 1 — Foundation
- [ ] Phase 2 — Identity/households/audit
- [ ] Phase 3 — Provider Policy Engine
- [ ] Phase 4 — Reference data/PostGIS
- [ ] Phase 5 — Core search/flexible dates/fake provider
- [ ] Phase 6 — Aviasales Data
- [ ] Phase 7 — Canonical offers/ranking/risk/total cost
- [ ] Phase 8 — Itinerary/split/self-transfer/hidden-city gating
- [ ] Phase 9 — Watches/scheduler/history
- [ ] Phase 10 — Price intelligence/deals/alerts
- [ ] Phase 11 — Telegram
- [ ] Phase 12 — Optional live providers
- [ ] Phase 13 — Full UI/PWA/i18n/accessibility
- [ ] Phase 14 — Security/operations/backups/observability
- [ ] Phase 15 — Release readiness

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

## Current slice

- Goal:
- Plan:
- Files/modules:
- ADR:
- Tests to add:
- Risks:

## Last verified commands

```text
not run yet
```

## Known external limitations

- None recorded yet.

## No-placeholder audit

- [ ] No TODO/pass/NotImplementedError in mandatory production paths
- [ ] No fake response in real provider paths
- [ ] No live provider calls in CI
- [ ] No secrets in repo/client/log fixtures
