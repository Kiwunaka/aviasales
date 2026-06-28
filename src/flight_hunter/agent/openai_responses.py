from __future__ import annotations

import json
from dataclasses import dataclass

import httpx2

from flight_hunter.agent.chat import IntentDraft

_ALLOWED_FIELDS = {
    "origin_query",
    "destination_query",
    "departure_date",
    "return_date",
    "date_hint",
    "wants_watch",
    "tool_plan",
}
_FORBIDDEN_FIELDS = {
    "price",
    "amount",
    "amount_minor",
    "currency_amount",
    "booking_url",
    "provider_offer_id",
    "flight_number",
    "airline",
    "availability",
}
_ALLOWED_TOOL_KINDS = {
    "resolve_airports",
    "build_date_matrix",
    "find_nearby_airports",
    "search_cached_offers",
    "propose_watch",
    "clarify_airport_choice",
    "clarify_travel_dates",
    "offer_live_check",
}


@dataclass(frozen=True, slots=True)
class OpenAIResponsesValidationResult:
    ok: bool
    draft: IntentDraft | None
    code: str | None = None


class OpenAIResponsesDraftValidator:
    def validate_json(self, raw_output: str) -> OpenAIResponsesValidationResult:
        try:
            payload = json.loads(raw_output)
        except json.JSONDecodeError:
            return OpenAIResponsesValidationResult(
                ok=False,
                draft=None,
                code="invalid_json",
            )
        return self.validate_payload(payload)

    def validate_payload(self, payload: object) -> OpenAIResponsesValidationResult:
        if not isinstance(payload, dict):
            return OpenAIResponsesValidationResult(ok=False, draft=None, code="invalid_payload")
        keys = set(payload)
        if keys & _FORBIDDEN_FIELDS or not keys <= _ALLOWED_FIELDS:
            return OpenAIResponsesValidationResult(
                ok=False,
                draft=None,
                code="forbidden_agent_fields",
            )
        if not _tool_plan_is_safe(payload.get("tool_plan")):
            return OpenAIResponsesValidationResult(
                ok=False,
                draft=None,
                code="forbidden_tool_plan",
            )

        return OpenAIResponsesValidationResult(
            ok=True,
            draft=IntentDraft(
                origin_query=_optional_string(payload.get("origin_query")),
                destination_query=_optional_string(payload.get("destination_query")),
                departure_date=_optional_string(payload.get("departure_date")),
                return_date=_optional_string(payload.get("return_date")),
                date_hint=_optional_string(payload.get("date_hint")),
                wants_watch=payload.get("wants_watch") is True,
            ),
        )


class OpenAIResponsesAgentAdapter:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: int,
        base_url: str = "https://api.openai.com",
        http_client: httpx2.Client | None = None,
        validator: OpenAIResponsesDraftValidator | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        if not model:
            raise ValueError("model is required")
        self._api_key = api_key
        self._model = model
        self._client = http_client or httpx2.Client(
            base_url=base_url,
            timeout=float(timeout_seconds),
        )
        self._validator = validator or OpenAIResponsesDraftValidator()

    @property
    def model(self) -> str:
        return self._model

    def build_request_payload(self, message: str) -> dict[str, object]:
        return {
            "model": self._model,
            "store": False,
            "parallel_tool_calls": False,
            "tool_choice": "auto",
            "instructions": _AGENT_INSTRUCTIONS,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": message,
                        }
                    ],
                }
            ],
            "tools": _tool_specs(),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "flight_hunter_agent_turn",
                    "strict": True,
                    "schema": _response_schema(),
                }
            },
        }

    def extract_intent(self, message: str) -> IntentDraft | None:
        try:
            response = self._client.post(
                "/v1/responses",
                json=self.build_request_payload(message),
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
            )
        except httpx2.HTTPError:
            return None
        if response.status_code >= 400:
            return None
        payload = response.json()
        if not isinstance(payload, dict):
            return None
        output_text = _extract_output_text(payload)
        if output_text is None:
            return None
        result = self._validator.validate_json(output_text)
        return result.draft if result.ok else None


_AGENT_INSTRUCTIONS = (
    "You are Flight Hunter's intent-planning agent. Extract travel intent and propose only safe "
    "tool plans. You are not a source of prices, schedules, availability, booking URLs, provider "
    "policies, or live facts. Never invent flights. Live/browser checks require user action. "
    "Return only the configured JSON schema."
)


def _tool_specs() -> list[dict[str, object]]:
    base_parameters: dict[str, object] = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }
    return [
        {
            "type": "function",
            "name": "resolve_airports",
            "description": "Resolve city or airport text into candidate airport options.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
                "additionalProperties": False,
            },
        },
        {
            "type": "function",
            "name": "build_date_matrix",
            "description": (
                "Build a provider-free flexible date matrix for exact user-selected dates."
            ),
            "parameters": base_parameters,
        },
        {
            "type": "function",
            "name": "find_nearby_airports",
            "description": "Find nearby airports from reference data only.",
            "parameters": base_parameters,
        },
        {
            "type": "function",
            "name": "search_cached_offers",
            "description": (
                "Run only policy-allowed cached offer search after required slots exist."
            ),
            "parameters": base_parameters,
        },
        {
            "type": "function",
            "name": "propose_watch",
            "description": (
                "Suggest or create a watch only when the user explicitly asked to monitor."
            ),
            "parameters": base_parameters,
        },
        {
            "type": "function",
            "name": "offer_live_check",
            "description": "Offer a user-action-only live check. Never execute live search itself.",
            "parameters": base_parameters,
        },
    ]


def _response_schema() -> dict[str, object]:
    nullable_string: dict[str, object] = {"type": ["string", "null"]}
    return {
        "type": "object",
        "properties": {
            "origin_query": nullable_string,
            "destination_query": nullable_string,
            "departure_date": nullable_string,
            "return_date": nullable_string,
            "date_hint": nullable_string,
            "wants_watch": {"type": "boolean"},
            "tool_plan": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string", "enum": sorted(_ALLOWED_TOOL_KINDS)},
                        "requires_user_action": {"type": "boolean"},
                    },
                    "required": ["kind", "requires_user_action"],
                    "additionalProperties": False,
                },
            },
        },
        "required": [
            "origin_query",
            "destination_query",
            "departure_date",
            "return_date",
            "date_hint",
            "wants_watch",
            "tool_plan",
        ],
        "additionalProperties": False,
    }


def _tool_plan_is_safe(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, list):
        return False
    for item in value:
        if not isinstance(item, dict):
            return False
        if set(item) - {"kind", "requires_user_action"}:
            return False
        kind = item.get("kind")
        if not isinstance(kind, str) or kind not in _ALLOWED_TOOL_KINDS:
            return False
        if type(item.get("requires_user_action")) is not bool:
            return False
        if kind == "offer_live_check" and item.get("requires_user_action") is not True:
            return False
    return True


def _optional_string(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _extract_output_text(payload: dict[str, object]) -> str | None:
    output_text = payload.get("output_text")
    if isinstance(output_text, str):
        return output_text
    output = payload.get("output")
    if not isinstance(output, list):
        return None
    chunks: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                chunks.append(part["text"])
    return "".join(chunks) if chunks else None
