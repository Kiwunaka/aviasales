from __future__ import annotations

from flight_hunter.notifications.telegram import (
    TelegramWebhookDecisionCode,
    TelegramWebhookHandler,
)


def test_telegram_webhook_rejects_when_disabled() -> None:
    handler = TelegramWebhookHandler(enabled=False, secret_token=None)

    decision = handler.handle_update(
        provided_secret=None,
        update={"update_id": 1001, "message": {"text": "/start"}},
    )

    assert decision.code == TelegramWebhookDecisionCode.DISABLED


def test_telegram_webhook_requires_matching_secret_when_enabled() -> None:
    handler = TelegramWebhookHandler(enabled=True, secret_token="secret")

    missing = handler.handle_update(
        provided_secret=None,
        update={"update_id": 1001, "message": {"text": "/start"}},
    )
    wrong = handler.handle_update(
        provided_secret="wrong",
        update={"update_id": 1001, "message": {"text": "/start"}},
    )
    accepted = handler.handle_update(
        provided_secret="secret",
        update={"update_id": 1001, "message": {"text": "/start"}},
    )

    assert missing.code == TelegramWebhookDecisionCode.SECRET_MISMATCH
    assert wrong.code == TelegramWebhookDecisionCode.SECRET_MISMATCH
    assert accepted.code == TelegramWebhookDecisionCode.ACCEPTED


def test_telegram_webhook_deduplicates_update_id() -> None:
    handler = TelegramWebhookHandler(enabled=True, secret_token="secret")

    first = handler.handle_update(
        provided_secret="secret",
        update={"update_id": 1001, "message": {"text": "/start"}},
    )
    second = handler.handle_update(
        provided_secret="secret",
        update={"update_id": 1001, "message": {"text": "/start"}},
    )

    assert first.code == TelegramWebhookDecisionCode.ACCEPTED
    assert second.code == TelegramWebhookDecisionCode.DUPLICATE
