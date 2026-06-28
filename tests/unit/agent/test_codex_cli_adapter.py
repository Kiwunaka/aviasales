from __future__ import annotations

from flight_hunter.agent.codex_cli import CodexCliAgentAdapter, CodexIntentDraftValidator


def test_codex_intent_validator_accepts_only_search_intent_fields() -> None:
    result = CodexIntentDraftValidator().validate_json(
        """
        {
          "origin_query": "Warsaw",
          "destination_query": "Barcelona",
          "departure_date": "2026-10-12",
          "return_date": "2026-10-19",
          "wants_watch": true
        }
        """
    )

    assert result.code == "valid"
    assert result.draft is not None
    assert result.draft.origin_query == "Warsaw"
    assert result.draft.wants_watch is True


def test_codex_intent_validator_rejects_prices_and_provider_facts() -> None:
    result = CodexIntentDraftValidator().validate_json(
        """
        {
          "origin_query": "Warsaw",
          "destination_query": "Barcelona",
          "departure_date": "2026-10-12",
          "amount_minor": 123400,
          "provider_offer_id": "made-up"
        }
        """
    )

    assert result.code == "forbidden_field"
    assert result.draft is None


def test_codex_cli_adapter_builds_sandboxed_ephemeral_command() -> None:
    adapter = CodexCliAgentAdapter(enabled=True, service_tier="fast", timeout_seconds=5)

    command = adapter.build_command(schema_path="C:/tmp/schema.json")

    assert command[:2] == ("codex", "exec")
    assert "--ephemeral" in command
    assert "--sandbox" in command
    assert "read-only" in command
    assert "-c" in command
    assert 'service_tier="fast"' in command
    assert "--output-schema" in command
