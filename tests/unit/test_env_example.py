from __future__ import annotations

from pathlib import Path


def test_env_example_exists_with_safe_placeholders() -> None:
    env_example = Path(".env.example")

    assert env_example.exists()

    content = env_example.read_text(encoding="utf-8")
    assert "AVIASALES_DATA_ENABLED=false" in content
    assert "TRAVELPAYOUTS_API_TOKEN=" in content
    assert "TRAVELPAYOUTS_API_TOKEN=72a" not in content
    assert "TELEGRAM_BOT_TOKEN=" in content
    assert "AGENT_PROVIDER=deterministic_presets" in content
    assert "AGENT_MCP_ENABLED=false" in content
    assert "AGENT_CODEX_CLI_ENABLED=false" in content
    assert "AGENT_CODEX_CLI_TIMEOUT_SECONDS=8" in content
    assert "AGENT_OPENAI_ENABLED=false" in content
    assert "AGENT_OPENAI_MODEL=gpt-5.5" in content
    assert "AGENT_OPENAI_TIMEOUT_SECONDS=8" in content
    assert "OPENAI_API_KEY=" in content
    assert "LIVE_REFRESH_MIN_GAP_SECONDS=600" in content
    assert "SCRAPING_OBSERVER_ENABLED=false" in content
    assert "SCRAPING_MIN_GAP_SECONDS=600" in content
    assert "PERSONAL_OBSERVER_ENABLED=false" in content
    assert "PERSONAL_OBSERVER_REQUIRE_USER_ACTION=true" in content
    assert "PERSONAL_OBSERVER_AUTO_RUN=false" in content
    assert "SCRAPLING_USE_FETCHERS=false" in content
    assert "CRAWL4AI_ENABLED=false" in content
    assert "SEARXNG_ENABLED=false" in content
    assert "RU_AGGREGATORS_ENABLED=aviasales_clickout,yandex_travel,tutu,onetwotrip" in content
    assert "CARRIER_LINKS_ENABLED=aeroflot,pobeda,s7" in content
    assert "SOURCE_INTERNAL_RPM=10" in content
