from __future__ import annotations

import json

import httpx2

from flight_hunter.agent.openai_responses import (
    OpenAIResponsesAgentAdapter,
    OpenAIResponsesDraftValidator,
)


def test_openai_agent_adapter_builds_responses_payload_with_tools_and_schema() -> None:
    adapter = OpenAIResponsesAgentAdapter(
        api_key="sk-test",
        model="gpt-5.5",
        timeout_seconds=7,
    )

    payload = adapter.build_request_payload("Хочу из спб улететь в Шанхай в октябре")

    assert payload["model"] == "gpt-5.5"
    assert payload["store"] is False
    assert payload["parallel_tool_calls"] is False
    assert payload["tool_choice"] == "auto"
    assert payload["text"]["format"]["type"] == "json_schema"
    assert payload["text"]["format"]["strict"] is True
    assert payload["text"]["format"]["name"] == "flight_hunter_agent_turn"
    assert {tool["name"] for tool in payload["tools"]} == {
        "resolve_airports",
        "build_date_matrix",
        "find_nearby_airports",
        "search_cached_offers",
        "propose_watch",
        "offer_live_check",
    }
    encoded = json.dumps(payload, ensure_ascii=False)
    assert "sk-test" not in encoded
    assert "booking_url" not in encoded
    assert "amount_minor" not in encoded


def test_openai_agent_validator_rejects_provider_facts_and_live_execution() -> None:
    validator = OpenAIResponsesDraftValidator()

    result = validator.validate_payload(
        {
            "origin_query": "Saint Petersburg",
            "destination_query": "Shanghai",
            "departure_date": None,
            "return_date": None,
            "date_hint": "октябрь",
            "wants_watch": False,
            "tool_plan": [
                {"kind": "resolve_airports", "requires_user_action": False},
                {"kind": "live_browser_search", "requires_user_action": False},
            ],
            "price": 12345,
        }
    )

    assert not result.ok
    assert result.code == "forbidden_agent_fields"


def test_openai_agent_validator_accepts_intent_and_safe_tool_plan() -> None:
    validator = OpenAIResponsesDraftValidator()

    result = validator.validate_payload(
        {
            "origin_query": "Saint Petersburg",
            "destination_query": "Shanghai",
            "departure_date": None,
            "return_date": None,
            "date_hint": "октябрь",
            "wants_watch": True,
            "tool_plan": [
                {"kind": "resolve_airports", "requires_user_action": False},
                {"kind": "clarify_travel_dates", "requires_user_action": True},
            ],
        }
    )

    assert result.ok
    assert result.draft is not None
    assert result.draft.origin_query == "Saint Petersburg"
    assert result.draft.destination_query == "Shanghai"
    assert result.draft.date_hint == "октябрь"
    assert result.draft.wants_watch is True


def test_openai_agent_adapter_falls_back_on_transport_error() -> None:
    adapter = OpenAIResponsesAgentAdapter(
        api_key="sk-test",
        model="gpt-5.5",
        timeout_seconds=7,
        http_client=_FailingClient(),
    )

    assert adapter.extract_intent("из СПб в Шанхай") is None


class _FailingClient:
    def post(self, *args: object, **kwargs: object) -> object:
        raise httpx2.ConnectError("network down")
