# ADR 0024: Agent chat, city search, and agent backend bridge

## Status

Accepted for current implementation slice.

## Context

The beginner UI has a visible assistant panel, but it only maps short prompts to deterministic
presets. The product needs a chat-first workflow where a user can type city names, dates, passenger
requirements, and monitoring intent in natural language. The assistant must then call deterministic
Flight Hunter tools, not invent prices or bypass provider rules.

The local Codex CLI can run as an optional agent backend, but it is not a provider contract
authority and must not receive provider secrets or trigger live/browser actions. The same boundary
also needs to support a hosted OpenAI Responses/Agents-style backend for natural-language intent
extraction without making the model a source of prices or provider policy.

OpenAI official docs checked on 2026-06-24:

- Agents SDK guide: `https://developers.openai.com/api/docs/guides/agents#build-with-the-sdk`
- Tools guide: `https://developers.openai.com/api/docs/guides/tools`

Cloudflare Agents SDK docs checked on 2026-06-24:

- Getting started: `https://raw.githubusercontent.com/cloudflare/agents/main/docs/getting-started.md`
- State: `https://raw.githubusercontent.com/cloudflare/agents/main/docs/state.md`
- Callable methods: `https://raw.githubusercontent.com/cloudflare/agents/main/docs/callable-methods.md`

OurAirports publishes UTF-8 CSV datasets as Public Domain data and states that the data is not
guaranteed accurate or fit for use. It is suitable as reference data with visible provenance and
admin correction later.

## Decision

- Add a typed `AgentChatService` as the orchestration boundary for chat turns.
- Keep deterministic parsing as the default behavior.
- Add an optional `CodexCliAgentAdapter` behind `AGENT_CODEX_CLI_ENABLED`; it may only return a
  typed intent draft and must run with timeout, ephemeral execution, schema validation, and no
  provider secrets.
- Add an optional `OpenAIResponsesAgentAdapter` behind `AGENT_OPENAI_ENABLED` and `OPENAI_API_KEY`.
  It sends only the user's current turn text, asks for strict JSON schema output, disables response
  storage, exposes only safe function-tool semantics, and discards invalid or unsafe output.
- Report agent runtime metadata in `/api/v1/agent/chat/turn` so the UI can show whether the current
  turn used deterministic fallback or OpenAI-backed intent extraction.
- Keep the application boundary compatible with a future Cloudflare `Agent`/WebSocket deployment,
  but do not migrate the FastAPI app in this slice. Durable edge state and callable methods are a
  future runtime decision, not a prerequisite for the local product path.
- Add SQLite-compatible airport/import tables and a local `airports.csv` importer before PostGIS.
- Add audit rows for agent actions without storing raw chat text.
- Let the agent create watches only when the user explicitly asks to track, monitor, or notify.
- Keep live/browser observation as a user-click action; the agent may render a live-check action
  card but cannot execute it by itself.

## Consequences

- The current FastAPI-served UI can become useful immediately without a Next.js migration.
- Production PostGIS import and admin override screens remain future slices.
- Codex CLI and OpenAI Responses integrations are available for operator experiments but the app
  remains functional without either.
- A model can improve parsing of fuzzy user text, but deterministic Flight Hunter services still
  resolve airports, plan dates, run cached search, create watches, and enforce live/provider policy.
- Provider/source expansion remains controlled by provider policy and future admin attestation.
