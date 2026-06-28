from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import cast

from flight_hunter.domain.policy import ExecutionContext, ProviderPolicy, require_aware_datetime


class McpValidationCode(StrEnum):
    VALID = "valid"
    INVALID_SHAPE = "invalid_shape"
    MISSING_FIELD = "missing_field"
    INVALID_MONEY = "invalid_money"
    INVALID_CURRENCY = "invalid_currency"
    INVALID_DATETIME = "invalid_datetime"


@dataclass(frozen=True, slots=True)
class McpPriceCandidate:
    source_id: str
    amount_minor: int
    currency: str
    observed_at: datetime
    requires_confirmation: bool

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id is required")
        if type(self.amount_minor) is not int or self.amount_minor < 0:
            raise ValueError("amount_minor must be a non-negative integer")
        if len(self.currency) != 3 or not self.currency.isupper():
            raise ValueError("currency must be an ISO 4217 alpha-3 code")
        require_aware_datetime(self.observed_at, "observed_at")


@dataclass(frozen=True, slots=True)
class McpValidationResult:
    code: McpValidationCode
    message: str
    candidates: tuple[McpPriceCandidate, ...]


@dataclass(frozen=True, slots=True)
class McpToolDecision:
    allowed: bool
    code: str
    message: str


class McpResponseValidator:
    def validate_price_candidates(self, payload: object) -> McpValidationResult:
        if not isinstance(payload, dict):
            return _validation_denial(McpValidationCode.INVALID_SHAPE)
        payload_map = cast("dict[str, object]", payload)
        raw_candidates = payload_map.get("candidates")
        if not isinstance(raw_candidates, list):
            return _validation_denial(McpValidationCode.INVALID_SHAPE)

        candidates: list[McpPriceCandidate] = []
        for raw_candidate in raw_candidates:
            if not isinstance(raw_candidate, dict):
                return _validation_denial(McpValidationCode.INVALID_SHAPE)
            candidate_map = cast("dict[str, object]", raw_candidate)
            required = (
                "source_id",
                "amount_minor",
                "currency",
                "observed_at",
                "requires_confirmation",
            )
            if any(field not in candidate_map for field in required):
                return _validation_denial(McpValidationCode.MISSING_FIELD)

            source_id = candidate_map["source_id"]
            amount_minor = candidate_map["amount_minor"]
            currency = candidate_map["currency"]
            observed_at = candidate_map["observed_at"]
            requires_confirmation = candidate_map["requires_confirmation"]

            if not isinstance(source_id, str) or not source_id:
                return _validation_denial(McpValidationCode.INVALID_SHAPE)
            if type(amount_minor) is not int or amount_minor < 0:
                return _validation_denial(McpValidationCode.INVALID_MONEY)
            if not isinstance(currency, str) or len(currency) != 3 or not currency.isupper():
                return _validation_denial(McpValidationCode.INVALID_CURRENCY)
            if not isinstance(observed_at, str):
                return _validation_denial(McpValidationCode.INVALID_DATETIME)
            if type(requires_confirmation) is not bool:
                return _validation_denial(McpValidationCode.INVALID_SHAPE)

            parsed_observed_at = _parse_aware_datetime(observed_at)
            if parsed_observed_at is None:
                return _validation_denial(McpValidationCode.INVALID_DATETIME)

            candidates.append(
                McpPriceCandidate(
                    source_id=source_id,
                    amount_minor=amount_minor,
                    currency=currency,
                    observed_at=parsed_observed_at,
                    requires_confirmation=requires_confirmation,
                )
            )

        return McpValidationResult(
            code=McpValidationCode.VALID,
            message="mcp output validated",
            candidates=tuple(candidates),
        )


class McpPolicyGateway:
    def authorize_tool_call(
        self,
        *,
        tool_name: str,
        provider_policy: ProviderPolicy,
        context: ExecutionContext,
        receives_secrets: bool,
    ) -> McpToolDecision:
        if receives_secrets:
            return McpToolDecision(
                allowed=False,
                code="mcp_secrets_denied",
                message="MCP tools cannot receive unrestricted provider secrets",
            )
        if context in {ExecutionContext.SCHEDULER, ExecutionContext.WORKER}:
            return McpToolDecision(
                allowed=False,
                code="mcp_background_denied",
                message="MCP cannot trigger background live/browser observations",
            )
        if not provider_policy.enabled:
            return McpToolDecision(
                allowed=False,
                code="provider_disabled",
                message="provider disabled",
            )
        if not provider_policy.credentials_present:
            return McpToolDecision(
                allowed=False,
                code="credentials_missing",
                message="credentials missing",
            )
        if not provider_policy.access_approved:
            return McpToolDecision(
                allowed=False,
                code="access_not_approved",
                message="access not approved",
            )
        if provider_policy.user_action_required:
            return McpToolDecision(
                allowed=False,
                code="mcp_user_action_required",
                message="MCP cannot bypass user action grants",
            )

        return McpToolDecision(
            allowed=True,
            code="allowed",
            message=f"MCP tool {tool_name} allowed by policy gateway",
        )


def _validation_denial(code: McpValidationCode) -> McpValidationResult:
    return McpValidationResult(code=code, message=code.value, candidates=())


def _parse_aware_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed
