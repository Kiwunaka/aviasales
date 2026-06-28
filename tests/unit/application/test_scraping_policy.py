from __future__ import annotations

from datetime import UTC, datetime

from flight_hunter.application.scraping_policy import (
    ScrapingObserverPolicy,
    ScrapingRequest,
    ScrapingStatusCode,
)

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)


def request(**overrides: object) -> ScrapingRequest:
    values: dict[str, object] = {
        "source_id": "example_source",
        "enabled": True,
        "permission_verified": True,
        "user_action": True,
        "background": False,
        "uses_captcha_solving": False,
        "uses_stealth": False,
        "uses_proxy_rotation": False,
        "uses_reused_cookies": False,
        "login_required": False,
    }
    values.update(overrides)
    return ScrapingRequest(**values)


def test_scraping_observer_is_denied_when_feature_flag_is_off() -> None:
    decision = ScrapingObserverPolicy().authorize(request(enabled=False))

    assert not decision.allowed
    assert decision.code == ScrapingStatusCode.FEATURE_DISABLED


def test_scraping_observer_requires_verified_source_permission() -> None:
    decision = ScrapingObserverPolicy().authorize(request(permission_verified=False))

    assert not decision.allowed
    assert decision.code == ScrapingStatusCode.PERMISSION_NOT_VERIFIED


def test_scraping_observer_requires_user_action_and_never_background() -> None:
    policy = ScrapingObserverPolicy()

    no_action = policy.authorize(request(user_action=False))
    background = policy.authorize(request(background=True))

    assert no_action.code == ScrapingStatusCode.USER_ACTION_REQUIRED
    assert background.code == ScrapingStatusCode.BACKGROUND_NOT_ALLOWED


def test_scraping_observer_blocks_prohibited_mechanisms() -> None:
    policy = ScrapingObserverPolicy()

    assert policy.authorize(request(uses_captcha_solving=True)).code == (
        ScrapingStatusCode.PROHIBITED_MECHANISM
    )
    assert policy.authorize(request(uses_stealth=True)).code == (
        ScrapingStatusCode.PROHIBITED_MECHANISM
    )
    assert policy.authorize(request(uses_proxy_rotation=True)).code == (
        ScrapingStatusCode.PROHIBITED_MECHANISM
    )
    assert policy.authorize(request(uses_reused_cookies=True)).code == (
        ScrapingStatusCode.PROHIBITED_MECHANISM
    )
    assert policy.authorize(request(login_required=True)).code == (
        ScrapingStatusCode.PROHIBITED_MECHANISM
    )


def test_scraping_observer_allows_plain_public_user_triggered_collection() -> None:
    decision = ScrapingObserverPolicy().authorize(request())

    assert decision.allowed
    assert decision.code == ScrapingStatusCode.ALLOWED
    assert decision.price_label == "observed_price"
