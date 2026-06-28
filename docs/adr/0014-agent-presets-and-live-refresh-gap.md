# ADR 0014: Agent Presets and Live Refresh Gap

Date: 2026-06-23

## Status

Accepted for the current backend slice.

## Context

Flight Hunter needs a beginner-friendly "agent mode" for travel tactics such as:

- best purchase timing;
- flexible dates;
- nearby airports;
- hidden-city research;
- split tickets;
- error fare sources;
- airline country/currency checks.

The same product also needs live prices, but provider rules prohibit treating live calls as background collection. Aviasales Search, Skyscanner Live, Duffel and similar providers stay disabled until credentials, access approval and contract flags are verified. Scraping public web pages is not a default data path.

Official references checked on 2026-06-23:

- Travelpayouts Aviasales Data API: https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API
- Travelpayouts API rate limits: https://support.travelpayouts.com/hc/en-us/articles/4402565416594-API-rate-limits
- OpenAI Codex MCP: https://developers.openai.com/codex/mcp
- OpenAI Codex CLI reference: https://developers.openai.com/codex/cli/reference
- OpenAI Codex authentication: https://developers.openai.com/codex/auth
- OpenAI Codex app server: https://developers.openai.com/codex/app-server

## Decision

1. Agent mode starts as deterministic presets, not a free-form autonomous browser or scraper.
2. Presets return a plan, required slots, risk level, warnings and policy-aware action descriptors.
3. The agent does not invent prices, schedules, airports or fare rules.
4. The agent may propose a live refresh only as a user action.
5. Live refresh has a minimum gap of 600 seconds by default.
6. Live refresh authorization combines provider policy, an unconsumed `UserActionGrant` and the refresh gap.
7. MCP/Codex configuration is represented as optional settings for future integration, but no external agent server is required for core behavior.

## Consequences

- Beginners get useful presets without needing OpenAI, Codex OAuth, MCP or provider keys.
- Future Codex CLI/server/MCP integrations can be attached behind the same typed plan boundary.
- Hidden-city and geo/currency flows are clearly marked as risky and never mixed into default ranking.
- Direct scraping of aggregator or airline pages remains out of scope unless explicit permission is verified and recorded in a provider contract.

## Verification

- `tests/unit/application/test_live_refresh.py`
- `tests/unit/agent/test_presets.py`
- `tests/unit/api/test_agent_api.py`
