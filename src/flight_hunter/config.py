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
        )

    @property
    def aviasales_data_credentials_present(self) -> bool:
        return self.travelpayouts_api_token is not None


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


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value
