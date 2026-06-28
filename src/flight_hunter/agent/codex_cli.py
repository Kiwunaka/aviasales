from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, cast

_ALLOWED_FIELDS = {
    "origin_query",
    "destination_query",
    "departure_date",
    "return_date",
    "wants_watch",
}
_FORBIDDEN_FIELDS = {
    "amount_minor",
    "price",
    "currency_price",
    "provider_offer_id",
    "booking_url",
    "booking_link",
    "freshness",
    "observed_at",
}


@dataclass(frozen=True, slots=True)
class CodexIntentDraft:
    origin_query: str | None = None
    destination_query: str | None = None
    departure_date: str | None = None
    return_date: str | None = None
    wants_watch: bool = False


@dataclass(frozen=True, slots=True)
class CodexIntentValidationResult:
    code: str
    message: str
    draft: CodexIntentDraft | None


class CodexIntentDraftValidator:
    def validate_json(self, raw_output: str) -> CodexIntentValidationResult:
        try:
            payload = json.loads(raw_output)
        except json.JSONDecodeError:
            return CodexIntentValidationResult(
                code="invalid_json",
                message="Codex output was not JSON",
                draft=None,
            )
        if not isinstance(payload, dict):
            return CodexIntentValidationResult(
                code="invalid_shape",
                message="Codex output must be an object",
                draft=None,
            )
        payload_map = cast("dict[str, object]", payload)
        if any(field in payload_map for field in _FORBIDDEN_FIELDS):
            return CodexIntentValidationResult(
                code="forbidden_field",
                message="Codex output cannot contain prices, provider facts, or booking data",
                draft=None,
            )
        if any(field not in _ALLOWED_FIELDS for field in payload_map):
            return CodexIntentValidationResult(
                code="unknown_field",
                message="Codex output contained an unsupported field",
                draft=None,
            )

        origin_query = _optional_str(payload_map.get("origin_query"))
        destination_query = _optional_str(payload_map.get("destination_query"))
        departure_date = _optional_str(payload_map.get("departure_date"))
        return_date = _optional_str(payload_map.get("return_date"))
        wants_watch = payload_map.get("wants_watch", False)
        if type(wants_watch) is not bool:
            return CodexIntentValidationResult(
                code="invalid_shape",
                message="wants_watch must be a boolean",
                draft=None,
            )

        return CodexIntentValidationResult(
            code="valid",
            message="Codex output validated",
            draft=CodexIntentDraft(
                origin_query=origin_query,
                destination_query=destination_query,
                departure_date=departure_date,
                return_date=return_date,
                wants_watch=wants_watch,
            ),
        )


class CodexCliAgentAdapter:
    def __init__(
        self,
        *,
        enabled: bool,
        service_tier: str = "fast",
        timeout_seconds: int = 8,
    ) -> None:
        self.enabled = enabled
        self.service_tier = service_tier if service_tier in {"fast", "flex"} else "fast"
        self.timeout_seconds = timeout_seconds

    def build_command(self, *, schema_path: str) -> tuple[str, ...]:
        return (
            "codex",
            "exec",
            "-c",
            f'service_tier="{self.service_tier}"',
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--output-schema",
            schema_path,
        )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
