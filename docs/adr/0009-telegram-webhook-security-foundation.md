# ADR 0009: Telegram Webhook Security Foundation

Date: 2026-06-23

## Status

Accepted.

## Context

Telegram production mode must use a webhook secret header and must deduplicate `update_id`. This can be implemented and tested without a real bot token or outbound Telegram calls.

## Decision

- Add a pure `TelegramWebhookHandler` that verifies enabled state, secret header and `update_id`.
- Add `POST /api/v1/telegram/webhook` as a thin delivery adapter.
- Keep Telegram disabled by default.
- Return stable machine-readable API codes while not exposing any bot token or webhook secret.
- Use in-process dedupe for this foundation slice; durable dedupe belongs to the future bot/worker persistence slice.

## Consequences

- Telegram webhook security can be tested locally without external credentials.
- Production still needs durable update storage, account linking, callback ownership checks and delivery queue before real alerts are enabled.
