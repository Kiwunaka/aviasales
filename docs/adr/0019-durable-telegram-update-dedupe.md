# ADR 0019: Durable Telegram Update Dedupe

Date: 2026-06-23

## Status

Accepted for the current backend slice.

## Context

Telegram can retry webhook updates. The previous foundation slice deduplicated `update_id` only in
process memory, which is insufficient after app restart or multiple workers. Production behavior
needs durable dedupe before future callback actions, alert acknowledgements or message delivery are
added.

## Decision

1. Add `telegram_update_dedupe` with `update_id` as the primary key and `received_at`.
2. Add `TelegramUpdateRepository.record_update(...) -> bool`.
3. Keep secret validation and update shape validation in the delivery boundary first.
4. Record accepted update IDs through the shared SQL session factory.
5. Return `duplicate` when the in-process handler or the SQL repository has already seen the
   update.
6. Do not process callback actions or send Telegram messages in this slice.

## Consequences

- Duplicate Telegram updates are ignored across app instances that share the same database.
- Webhook responses remain stable: accepted updates return `202`, duplicates return `200`.
- Telegram account linking, ownership checks and delivery queue remain pending.

## Verification

- `tests/unit/persistence/test_telegram_update_repository.py`
- `tests/unit/api/test_telegram_api.py`
- `tests/unit/persistence/test_alembic_upgrade.py`
