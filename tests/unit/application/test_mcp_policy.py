from __future__ import annotations

from datetime import UTC, datetime

from flight_hunter.application.mcp_policy import (
    McpPolicyGateway,
    McpPriceCandidate,
    McpResponseValidator,
    McpValidationCode,
)
from flight_hunter.domain.policy import ExecutionContext, ProviderPolicy

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)


def test_mcp_validator_accepts_typed_price_candidate_with_minor_units() -> None:
    result = McpResponseValidator().validate_price_candidates(
        {
            "candidates": [
                {
                    "source_id": "manual_feed",
                    "amount_minor": 123400,
                    "currency": "RUB",
                    "observed_at": "2026-06-23T12:00:00+00:00",
                    "requires_confirmation": True,
                }
            ]
        }
    )

    assert result.code == McpValidationCode.VALID
    assert result.candidates == (
        McpPriceCandidate(
            source_id="manual_feed",
            amount_minor=123400,
            currency="RUB",
            observed_at=NOW,
            requires_confirmation=True,
        ),
    )


def test_mcp_validator_rejects_float_money_and_missing_confirmation_flag() -> None:
    validator = McpResponseValidator()

    float_result = validator.validate_price_candidates(
        {
            "candidates": [
                {
                    "source_id": "manual_feed",
                    "amount_minor": 1234.5,
                    "currency": "RUB",
                    "observed_at": "2026-06-23T12:00:00+00:00",
                    "requires_confirmation": True,
                }
            ]
        }
    )
    missing_flag = validator.validate_price_candidates(
        {
            "candidates": [
                {
                    "source_id": "manual_feed",
                    "amount_minor": 123400,
                    "currency": "RUB",
                    "observed_at": "2026-06-23T12:00:00+00:00",
                }
            ]
        }
    )

    assert float_result.code == McpValidationCode.INVALID_MONEY
    assert missing_flag.code == McpValidationCode.MISSING_FIELD


def test_mcp_gateway_cannot_trigger_background_or_bypass_provider_policy() -> None:
    gateway = McpPolicyGateway()
    policy = ProviderPolicy.aviasales_search(
        terms_verified_at=NOW,
        credentials_present=False,
        access_approved=False,
        enabled=False,
    )

    background = gateway.authorize_tool_call(
        tool_name="browser_observe",
        provider_policy=policy,
        context=ExecutionContext.WORKER,
        receives_secrets=False,
    )
    provider_denied = gateway.authorize_tool_call(
        tool_name="search_api",
        provider_policy=policy,
        context=ExecutionContext.WEB_USER_ACTION,
        receives_secrets=False,
    )
    secrets = gateway.authorize_tool_call(
        tool_name="search_api",
        provider_policy=policy,
        context=ExecutionContext.WEB_USER_ACTION,
        receives_secrets=True,
    )

    assert not background.allowed
    assert background.code == "mcp_background_denied"
    assert not provider_denied.allowed
    assert provider_denied.code == "provider_disabled"
    assert not secrets.allowed
    assert secrets.code == "mcp_secrets_denied"
