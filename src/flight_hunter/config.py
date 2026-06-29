from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppSettings:
    database_url: str
    aviasales_data_enabled: bool
    travelpayouts_api_token: str | None
    aviasales_data_default_market: str
    aviasales_data_internal_rpm: int
    telegram_enabled: bool
    telegram_webhook_secret: str | None
    live_refresh_min_gap_seconds: int = 600
    agent_mode_enabled: bool = True
    agent_provider: str = "deterministic_presets"
    agent_mcp_enabled: bool = False
    agent_mcp_server: str | None = None
    agent_codex_cli_enabled: bool = False
    agent_codex_cli_timeout_seconds: int = 8
    agent_codex_cli_service_tier: str = "fast"
    agent_openai_enabled: bool = False
    agent_openai_model: str = "gpt-5.5"
    agent_openai_timeout_seconds: int = 8
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com"
    scraping_observer_enabled: bool = False
    scraping_min_gap_seconds: int = 600
    personal_observer_enabled: bool = False
    personal_observer_headless: bool = False
    personal_observer_profile_root: str = ".local/browser-profiles"
    personal_observer_save_dom_fixtures: bool = False
    personal_observer_save_screenshots: bool = False
    personal_observer_max_concurrent: int = 1
    personal_observer_min_gap_seconds: int = 60
    personal_observer_result_ttl_seconds: int = 300
    personal_observer_allowed_hosts: tuple[str, ...] = (
        "aviasales.ru",
        "www.aviasales.ru",
        "travel.yandex.ru",
        "www.tutu.ru",
        "avia.tutu.ru",
        "www.onetwotrip.com",
    )
    personal_observer_require_user_action: bool = True
    personal_observer_auto_run: bool = False
    scrapling_enabled: bool = True
    scrapling_adaptive_storage: str = ".local/scrapling-adaptive"
    scrapling_use_fetchers: bool = False
    scrapling_use_spiders: bool = False
    crawl4ai_enabled: bool = False
    crawl4ai_mode: str = "library"
    crawl4ai_cache_dir: str = ".local/crawl4ai-cache"
    searxng_enabled: bool = False
    searxng_base_url: str = "http://127.0.0.1:8080"
    searxng_format: str = "json"
    searxng_timeout_seconds: int = 15
    ru_aggregators_enabled: tuple[str, ...] = (
        "aviasales_clickout",
        "yandex_travel",
        "tutu",
        "onetwotrip",
    )
    carrier_links_enabled: tuple[str, ...] = ("aeroflot", "pobeda", "s7")
    source_internal_rpm: int = 10

    @classmethod
    def from_env(cls) -> AppSettings:
        return cls(
            database_url=os.getenv(
                "DATABASE_URL",
                "sqlite+aiosqlite:///./flight_hunter_dev.db",
            ),
            live_refresh_min_gap_seconds=_env_int("LIVE_REFRESH_MIN_GAP_SECONDS", default=600),
            agent_mode_enabled=_env_bool("AGENT_MODE_ENABLED", default=True),
            agent_provider=os.getenv("AGENT_PROVIDER", "deterministic_presets"),
            agent_mcp_enabled=_env_bool("AGENT_MCP_ENABLED", default=False),
            agent_mcp_server=_env_optional("AGENT_MCP_SERVER"),
            agent_codex_cli_enabled=_env_bool("AGENT_CODEX_CLI_ENABLED", default=False),
            agent_codex_cli_timeout_seconds=_env_int(
                "AGENT_CODEX_CLI_TIMEOUT_SECONDS",
                default=8,
            ),
            agent_codex_cli_service_tier=os.getenv("AGENT_CODEX_CLI_SERVICE_TIER", "fast"),
            agent_openai_enabled=_env_bool("AGENT_OPENAI_ENABLED", default=False),
            agent_openai_model=os.getenv("AGENT_OPENAI_MODEL", "gpt-5.5"),
            agent_openai_timeout_seconds=_env_int(
                "AGENT_OPENAI_TIMEOUT_SECONDS",
                default=8,
            ),
            openai_api_key=_env_optional("OPENAI_API_KEY"),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com"),
            aviasales_data_enabled=_env_bool("AVIASALES_DATA_ENABLED", default=False),
            travelpayouts_api_token=_env_optional("TRAVELPAYOUTS_API_TOKEN"),
            aviasales_data_default_market=os.getenv("AVIASALES_DATA_DEFAULT_MARKET", "pl"),
            aviasales_data_internal_rpm=_env_int("AVIASALES_DATA_INTERNAL_RPM", default=30),
            telegram_enabled=_env_bool("TELEGRAM_ENABLED", default=False),
            telegram_webhook_secret=_env_optional("TELEGRAM_WEBHOOK_SECRET"),
            scraping_observer_enabled=_env_bool("SCRAPING_OBSERVER_ENABLED", default=False),
            scraping_min_gap_seconds=_env_int("SCRAPING_MIN_GAP_SECONDS", default=600),
            personal_observer_enabled=_env_bool("PERSONAL_OBSERVER_ENABLED", default=False),
            personal_observer_headless=_env_bool("PERSONAL_OBSERVER_HEADLESS", default=False),
            personal_observer_profile_root=os.getenv(
                "PERSONAL_OBSERVER_PROFILE_ROOT",
                ".local/browser-profiles",
            ),
            personal_observer_save_dom_fixtures=_env_bool(
                "PERSONAL_OBSERVER_SAVE_DOM_FIXTURES",
                default=False,
            ),
            personal_observer_save_screenshots=_env_bool(
                "PERSONAL_OBSERVER_SAVE_SCREENSHOTS",
                default=False,
            ),
            personal_observer_max_concurrent=_env_int(
                "PERSONAL_OBSERVER_MAX_CONCURRENT",
                default=1,
            ),
            personal_observer_min_gap_seconds=_env_int(
                "PERSONAL_OBSERVER_MIN_GAP_SECONDS",
                default=60,
            ),
            personal_observer_result_ttl_seconds=_env_int(
                "PERSONAL_OBSERVER_RESULT_TTL_SECONDS",
                default=300,
            ),
            personal_observer_allowed_hosts=_env_csv(
                "PERSONAL_OBSERVER_ALLOWED_HOSTS",
                default=(
                    "aviasales.ru",
                    "www.aviasales.ru",
                    "travel.yandex.ru",
                    "www.tutu.ru",
                    "avia.tutu.ru",
                    "www.onetwotrip.com",
                ),
            ),
            personal_observer_require_user_action=_env_bool(
                "PERSONAL_OBSERVER_REQUIRE_USER_ACTION",
                default=True,
            ),
            personal_observer_auto_run=_env_bool(
                "PERSONAL_OBSERVER_AUTO_RUN",
                default=False,
            ),
            scrapling_enabled=_env_bool("SCRAPLING_ENABLED", default=True),
            scrapling_adaptive_storage=os.getenv(
                "SCRAPLING_ADAPTIVE_STORAGE",
                ".local/scrapling-adaptive",
            ),
            scrapling_use_fetchers=_env_bool("SCRAPLING_USE_FETCHERS", default=False),
            scrapling_use_spiders=_env_bool("SCRAPLING_USE_SPIDERS", default=False),
            crawl4ai_enabled=_env_bool("CRAWL4AI_ENABLED", default=False),
            crawl4ai_mode=os.getenv("CRAWL4AI_MODE", "library"),
            crawl4ai_cache_dir=os.getenv("CRAWL4AI_CACHE_DIR", ".local/crawl4ai-cache"),
            searxng_enabled=_env_bool("SEARXNG_ENABLED", default=False),
            searxng_base_url=os.getenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080"),
            searxng_format=os.getenv("SEARXNG_FORMAT", "json"),
            searxng_timeout_seconds=_env_int("SEARXNG_TIMEOUT_SECONDS", default=15),
            ru_aggregators_enabled=_env_csv(
                "RU_AGGREGATORS_ENABLED",
                default=("aviasales_clickout", "yandex_travel", "tutu", "onetwotrip"),
            ),
            carrier_links_enabled=_env_csv(
                "CARRIER_LINKS_ENABLED",
                default=("aeroflot", "pobeda", "s7"),
            ),
            source_internal_rpm=_env_int("SOURCE_INTERNAL_RPM", default=10),
        )

    @property
    def aviasales_data_credentials_present(self) -> bool:
        return self.travelpayouts_api_token is not None

    @property
    def ru_clickout_enabled_source_ids(self) -> tuple[str, ...]:
        return (*self.ru_aggregators_enabled, *self.carrier_links_enabled)


def load_env_file(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_quotes(value.strip())
        if key and key not in os.environ:
            os.environ[key] = value


def _env_optional(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    return value.strip()


def _env_bool(name: str, *, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, *, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return parsed


def _env_csv(name: str, *, default: tuple[str, ...]) -> tuple[str, ...]:
    value = os.getenv(name)
    if value is None:
        return default
    if not value.strip():
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value
