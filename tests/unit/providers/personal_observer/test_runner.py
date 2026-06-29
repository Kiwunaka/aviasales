from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from flight_hunter.domain.money import Money
from flight_hunter.domain.offers import SearchIntent
from flight_hunter.domain.search_results import Confidence
from flight_hunter.providers.personal_observer.runner import (
    PersonalObserverConfig,
    PersonalObserverError,
    PersonalObserverErrorCode,
    PersonalObserverRunner,
)

NOW = datetime(2026, 6, 29, 15, 0, tzinfo=UTC)
FIXTURE = Path("tests/fixtures/browser/tutu/search_result_sanitized.html")


def test_runner_observes_fixture_without_live_browser_enabled(tmp_path: Path) -> None:
    runner = PersonalObserverRunner(
        config=_config(tmp_path, enabled=False),
        clock=lambda: NOW,
    )

    result = runner.observe(
        source_id="tutu",
        intent=_intent(),
        user_action=True,
        fixture_html_path=FIXTURE,
    )

    assert result.source_id == "tutu"
    assert result.extraction.confidence == Confidence.MEDIUM
    assert result.extraction.offers[0].total_price == Money(1_842_000, "RUB")
    assert result.extraction.offers[0].observed_at == NOW


def test_runner_rejects_live_browser_when_observer_disabled(tmp_path: Path) -> None:
    runner = PersonalObserverRunner(
        config=_config(tmp_path, enabled=False),
        clock=lambda: NOW,
    )

    with pytest.raises(PersonalObserverError) as exc:
        runner.observe(
            source_id="tutu",
            intent=_intent(),
            user_action=True,
            fixture_html_path=None,
        )

    assert exc.value.code == PersonalObserverErrorCode.OBSERVER_DISABLED


def test_runner_rejects_sources_without_browser_observation_permission(tmp_path: Path) -> None:
    runner = PersonalObserverRunner(config=_config(tmp_path), clock=lambda: NOW)

    with pytest.raises(PersonalObserverError) as exc:
        runner.observe(
            source_id="aviasales_clickout",
            intent=_intent(),
            user_action=True,
            fixture_html_path=FIXTURE,
        )

    assert exc.value.code == PersonalObserverErrorCode.SOURCE_NOT_OBSERVABLE


def test_runner_rejects_hosts_outside_allowlist(tmp_path: Path) -> None:
    runner = PersonalObserverRunner(
        config=_config(tmp_path, allowed_hosts=("travel.yandex.ru",)),
        clock=lambda: NOW,
    )

    with pytest.raises(PersonalObserverError) as exc:
        runner.observe(
            source_id="tutu",
            intent=_intent(),
            user_action=True,
            fixture_html_path=FIXTURE,
        )

    assert exc.value.code == PersonalObserverErrorCode.HOST_NOT_ALLOWED


def _intent() -> SearchIntent:
    return SearchIntent(
        origin="MOW",
        destination="IST",
        departure_date="2026-09-10",
        return_date="2026-09-20",
        passengers=1,
        currency="RUB",
    )


def _config(
    tmp_path: Path,
    *,
    enabled: bool = True,
    allowed_hosts: tuple[str, ...] = ("www.tutu.ru", "tutu.ru", "avia.tutu.ru"),
) -> PersonalObserverConfig:
    return PersonalObserverConfig(
        enabled=enabled,
        headless=False,
        profile_root=tmp_path / "profiles",
        save_dom_fixtures=False,
        save_screenshots=False,
        allowed_hosts=allowed_hosts,
    )
