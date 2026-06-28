# ADR 0008: FastAPI Served Beginner Web UI

Date: 2026-06-23

## Status

Accepted.

## Context

The project needs to be usable by a beginner before the full Next.js/PWA layer exists. Requiring the user to operate only through OpenAPI docs is functional but not friendly.

## Decision

- Serve a small HTML/CSS/JavaScript web UI from FastAPI at `GET /`.
- Use existing JSON endpoints for provider status and search results.
- Keep the UI simple: one search form, provider status, and results with freshness/caveat labels.
- Translate provider and denial codes into plain visible Russian labels in the UI while keeping machine-readable API codes unchanged.
- Defer full Next.js/PWA architecture until a later frontend slice.

## Consequences

- The current app can be opened directly at `http://127.0.0.1:8000/`.
- No separate Node frontend toolchain is required for the beginner demo screen.
- The UI remains a foundation, not the final production PWA.
