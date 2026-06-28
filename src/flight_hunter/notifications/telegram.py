from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class TelegramWebhookDecisionCode(StrEnum):
    ACCEPTED = "accepted"
    DISABLED = "telegram_disabled"
    DUPLICATE = "duplicate"
    INVALID_UPDATE = "invalid_update"
    SECRET_MISMATCH = "secret_mismatch"


@dataclass(frozen=True, slots=True)
class TelegramWebhookDecision:
    code: TelegramWebhookDecisionCode


@dataclass(slots=True)
class TelegramWebhookHandler:
    enabled: bool
    secret_token: str | None
    _seen_update_ids: set[int] = field(default_factory=set)

    def handle_update(
        self,
        *,
        provided_secret: str | None,
        update: Mapping[str, object],
    ) -> TelegramWebhookDecision:
        if not self.enabled:
            return TelegramWebhookDecision(TelegramWebhookDecisionCode.DISABLED)
        if self.secret_token is None or provided_secret != self.secret_token:
            return TelegramWebhookDecision(TelegramWebhookDecisionCode.SECRET_MISMATCH)

        update_id = update.get("update_id")
        if type(update_id) is not int:
            return TelegramWebhookDecision(TelegramWebhookDecisionCode.INVALID_UPDATE)
        if update_id in self._seen_update_ids:
            return TelegramWebhookDecision(TelegramWebhookDecisionCode.DUPLICATE)

        self._seen_update_ids.add(update_id)
        return TelegramWebhookDecision(TelegramWebhookDecisionCode.ACCEPTED)
