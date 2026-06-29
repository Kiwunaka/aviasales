from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlparse

from flight_hunter.browser.html_extractor import (
    BrowserExtractionResult,
    DomSnapshot,
    GenericRuHtmlOfferExtractor,
)
from flight_hunter.config import AppSettings
from flight_hunter.domain.offers import SearchIntent
from flight_hunter.providers.ru_clickout import RuClickoutLinkBuilder, default_ru_aggregator_specs
from flight_hunter.providers.ru_clickout.source_specs import RuAggregatorSpec


class PersonalObserverErrorCode(StrEnum):
    OBSERVER_DISABLED = "observer_disabled"
    SOURCE_NOT_FOUND = "source_not_found"
    SOURCE_NOT_OBSERVABLE = "source_not_observable"
    HOST_NOT_ALLOWED = "host_not_allowed"
    PLAYWRIGHT_UNAVAILABLE = "playwright_unavailable"
    NAVIGATION_FAILED = "navigation_failed"
    PARSER_NO_OFFERS = "parser_no_offers"


class PersonalObserverError(RuntimeError):
    def __init__(self, code: PersonalObserverErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True, slots=True)
class PersonalObserverConfig:
    enabled: bool
    headless: bool
    profile_root: Path
    save_dom_fixtures: bool
    save_screenshots: bool
    allowed_hosts: tuple[str, ...]
    require_user_action: bool = True
    navigation_timeout_ms: int = 45_000

    @classmethod
    def from_settings(cls, settings: AppSettings) -> PersonalObserverConfig:
        return cls(
            enabled=settings.personal_observer_enabled,
            headless=settings.personal_observer_headless,
            profile_root=Path(settings.personal_observer_profile_root),
            save_dom_fixtures=settings.personal_observer_save_dom_fixtures,
            save_screenshots=settings.personal_observer_save_screenshots,
            allowed_hosts=settings.personal_observer_allowed_hosts,
            require_user_action=settings.personal_observer_require_user_action,
        )


@dataclass(frozen=True, slots=True)
class PersonalObserverResult:
    source_id: str
    final_url: str
    snapshot: DomSnapshot
    extraction: BrowserExtractionResult


class PersonalObserverRunner:
    def __init__(
        self,
        *,
        config: PersonalObserverConfig,
        specs: Sequence[RuAggregatorSpec] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._config = config
        self._specs = tuple(specs or default_ru_aggregator_specs())
        self._spec_by_id = {spec.source_id: spec for spec in self._specs}
        self._clock = clock or (lambda: datetime.now(UTC))
        self._link_builder = RuClickoutLinkBuilder(self._specs)

    def observe(
        self,
        *,
        source_id: str,
        intent: SearchIntent,
        user_action: bool,
        fixture_html_path: Path | None = None,
    ) -> PersonalObserverResult:
        spec = self._spec_by_id.get(source_id)
        if spec is None:
            raise PersonalObserverError(
                PersonalObserverErrorCode.SOURCE_NOT_FOUND,
                "source not found",
            )
        if not spec.browser_observation_allowed:
            raise PersonalObserverError(
                PersonalObserverErrorCode.SOURCE_NOT_OBSERVABLE,
                "source does not allow browser observation",
            )
        link = self._link_builder.build(spec, intent)
        self._validate_allowed_host(link.url)

        if fixture_html_path is not None:
            html = fixture_html_path.read_text(encoding="utf-8")
            snapshot = DomSnapshot.from_html(
                source_id=source_id,
                final_url=link.url,
                html=html,
                captured_at=self._clock(),
                title=f"fixture:{fixture_html_path.name}",
            )
        else:
            self._validate_live_run_allowed(user_action=user_action)
            snapshot = self._capture_with_playwright(source_id=source_id, url=link.url)

        extractor = GenericRuHtmlOfferExtractor(source_names={source_id: spec.display_name})
        extraction = extractor.extract(snapshot, intent)
        if not extraction.offers:
            raise PersonalObserverError(
                PersonalObserverErrorCode.PARSER_NO_OFFERS,
                "parser did not extract any offers",
            )
        return PersonalObserverResult(
            source_id=source_id,
            final_url=snapshot.final_url,
            snapshot=snapshot,
            extraction=extraction,
        )

    def _validate_live_run_allowed(self, *, user_action: bool) -> None:
        if not self._config.enabled:
            raise PersonalObserverError(
                PersonalObserverErrorCode.OBSERVER_DISABLED,
                "personal observer is disabled",
            )
        if self._config.require_user_action and not user_action:
            raise PersonalObserverError(
                PersonalObserverErrorCode.OBSERVER_DISABLED,
                "personal observer requires explicit user action",
            )

    def _validate_allowed_host(self, url: str) -> None:
        host = urlparse(url).netloc.lower()
        if host not in self._config.allowed_hosts:
            raise PersonalObserverError(
                PersonalObserverErrorCode.HOST_NOT_ALLOWED,
                f"host is not allowed: {host}",
            )

    def _capture_with_playwright(self, *, source_id: str, url: str) -> DomSnapshot:
        try:
            from playwright.sync_api import Error as PlaywrightError
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise PersonalObserverError(
                PersonalObserverErrorCode.PLAYWRIGHT_UNAVAILABLE,
                "playwright is not installed; sync the scraping dependency group",
            ) from exc

        profile_dir = self._config.profile_root / source_id
        profile_dir.mkdir(parents=True, exist_ok=True)
        try:
            with sync_playwright() as playwright:
                context = playwright.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    headless=self._config.headless,
                    accept_downloads=False,
                )
                page = context.new_page()
                page.goto(
                    url, wait_until="domcontentloaded", timeout=self._config.navigation_timeout_ms
                )
                page.wait_for_timeout(1500)
                final_url = page.url
                self._validate_allowed_host(final_url)
                html = page.content()
                title = page.title()
                screenshot_path = None
                if self._config.save_screenshots:
                    screenshot_path = str(profile_dir / f"{_timestamp(self._clock())}.png")
                    page.screenshot(path=screenshot_path, full_page=True)
                context.close()
        except (PlaywrightError, PlaywrightTimeoutError) as exc:
            raise PersonalObserverError(
                PersonalObserverErrorCode.NAVIGATION_FAILED,
                "browser navigation failed",
            ) from exc

        if self._config.save_dom_fixtures:
            fixture_path = profile_dir / f"{_timestamp(self._clock())}.html"
            fixture_path.write_text(html, encoding="utf-8")

        return DomSnapshot.from_html(
            source_id=source_id,
            final_url=final_url,
            title=title,
            html=html,
            captured_at=self._clock(),
            screenshot_path=screenshot_path,
        )


def _timestamp(value: datetime) -> str:
    return value.strftime("%Y%m%dT%H%M%SZ")
