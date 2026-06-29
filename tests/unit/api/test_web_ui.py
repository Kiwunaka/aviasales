# ruff: noqa: RUF001

from __future__ import annotations

import re

from fastapi.testclient import TestClient

from flight_hunter.api.app import create_app


def test_root_serves_beginner_friendly_search_screen_without_secrets() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Flight Hunter" in response.text
    assert 'id="search-form"' in response.text
    assert "/api/v1/providers" in response.text
    assert "/api/v1/searches" in response.text
    assert "/api/v1/browser-sources" in response.text
    assert "/api/v1/live-observation-grants" in response.text
    assert "/api/v1/live-observations" in response.text
    assert "/api/v1/agent/presets" in response.text
    assert "/api/v1/agent/plan" in response.text
    assert "/api/v1/agent/chat/turn" in response.text
    assert "/api/v1/airports/search" in response.text
    assert "agent-cockpit" in response.text
    assert 'id="runtime-strip"' in response.text
    assert 'id="agent-runtime"' in response.text
    assert 'id="agent-live-policy"' in response.text
    assert 'id="decision-rail"' in response.text
    assert "Human-in-the-loop" in response.text
    assert "Agent cockpit" in response.text
    assert "function renderAgentRuntime" in response.text
    assert 'document.createTextNode("\\n")' in response.text
    assert "flight_hunter_demo_household_id" in response.text
    assert "X-Flight-Hunter-Household-Id" in response.text
    assert "X-Flight-Hunter-User-Id" in response.text
    assert 'id="airport-choice-list"' in response.text
    assert 'id="agent-action-list"' in response.text
    assert "Взрослые" in response.text
    assert "Проверить live" in response.text
    assert "ranking_reasons" in response.text
    assert "priced_offers" in response.text
    assert "external_links" in response.text
    assert "browser_observed_offers" in response.text
    assert "freshness_summary" in response.text
    assert "Цены из кэша" in response.text
    assert "Ссылки для проверки" in response.text
    assert "Свежие наблюдения из браузера" in response.text
    assert "function providerHelp" in response.text
    assert "function syncExtractedRoute" in response.text
    assert "Не подключен" in response.text
    assert "API key" in response.text
    assert 'join("\\n\\n")' in response.text
    assert 'join("\n\n")' not in response.text
    assert "grant_token" not in response.text
    assert "TRAVELPAYOUTS_API_TOKEN" not in response.text
    assert "secret" not in response.text.lower()
    assert not re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        response.text,
        flags=re.IGNORECASE,
    )
