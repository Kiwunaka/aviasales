from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ScrapingStatusCode(StrEnum):
    ALLOWED = "allowed"
    BACKGROUND_NOT_ALLOWED = "background_not_allowed"
    FEATURE_DISABLED = "feature_disabled"
    PERMISSION_NOT_VERIFIED = "permission_not_verified"
    PROHIBITED_MECHANISM = "prohibited_mechanism"
    USER_ACTION_REQUIRED = "user_action_required"


@dataclass(frozen=True, slots=True)
class ScrapingRequest:
    source_id: str
    enabled: bool
    permission_verified: bool
    user_action: bool
    background: bool
    uses_captcha_solving: bool
    uses_stealth: bool
    uses_proxy_rotation: bool
    uses_reused_cookies: bool
    login_required: bool

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id is required")


@dataclass(frozen=True, slots=True)
class ScrapingDecision:
    source_id: str
    allowed: bool
    code: ScrapingStatusCode
    message: str
    price_label: str


class ScrapingObserverPolicy:
    def authorize(self, request: ScrapingRequest) -> ScrapingDecision:
        if not request.enabled:
            return self._deny(request, ScrapingStatusCode.FEATURE_DISABLED)
        if not request.permission_verified:
            return self._deny(request, ScrapingStatusCode.PERMISSION_NOT_VERIFIED)
        if not request.user_action:
            return self._deny(request, ScrapingStatusCode.USER_ACTION_REQUIRED)
        if request.background:
            return self._deny(request, ScrapingStatusCode.BACKGROUND_NOT_ALLOWED)
        if (
            request.uses_captcha_solving
            or request.uses_stealth
            or request.uses_proxy_rotation
            or request.uses_reused_cookies
            or request.login_required
        ):
            return self._deny(request, ScrapingStatusCode.PROHIBITED_MECHANISM)

        return ScrapingDecision(
            source_id=request.source_id,
            allowed=True,
            code=ScrapingStatusCode.ALLOWED,
            message="plain public user-triggered observer allowed",
            price_label="observed_price",
        )

    @staticmethod
    def _deny(request: ScrapingRequest, code: ScrapingStatusCode) -> ScrapingDecision:
        return ScrapingDecision(
            source_id=request.source_id,
            allowed=False,
            code=code,
            message=code.value,
            price_label="not_collected",
        )
