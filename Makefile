.PHONY: help bootstrap dev dev-api test test-unit lint typecheck migrate quality provider-contracts travelpayouts-smoke backup restore cleanup-live-observations import-airports

help:
	@echo "Flight Hunter commands:"
	@echo "  make bootstrap          Install dev dependencies with uv"
	@echo "  make dev                Run the local demo API and web screen"
	@echo "  make dev-api            Run the local demo API"
	@echo "  make test               Run current automated tests"
	@echo "  make test-unit          Run unit tests"
	@echo "  make lint               Run formatter check and lint"
	@echo "  make typecheck          Run mypy"
	@echo "  make migrate            Apply Alembic migrations"
	@echo "  make quality            Run test, lint, and typecheck"
	@echo "  make provider-contracts Run current policy contract tests"
	@echo "  make travelpayouts-smoke Run one sanitized Aviasales Data API smoke check"
	@echo "  make backup             Back up local SQLite demo database"
	@echo "  make restore BACKUP=... Restore local SQLite demo database"
	@echo "  make cleanup-live-observations Clean expired live-check demo state"
	@echo "  make import-airports AIRPORTS_CSV=... Import OurAirports airports.csv"

bootstrap:
	uv sync --group dev

dev: dev-api

dev-api:
	uv run uvicorn flight_hunter.api.app:app --reload --host 127.0.0.1 --port 8000

test: test-unit

test-unit:
	uv run pytest tests/unit

lint:
	uv run ruff format --check .
	uv run ruff check .

typecheck:
	uv run mypy

migrate:
	uv run alembic upgrade head

quality: test lint typecheck

provider-contracts:
	uv run pytest tests/unit/policy

travelpayouts-smoke:
	uv run travelpayouts-smoke

backup:
	uv run flight-hunter-backup

restore:
	uv run flight-hunter-restore "$(BACKUP)"

cleanup-live-observations:
	uv run flight-hunter-cleanup-live-observations

import-airports:
	uv run flight-hunter-import-airports --airports-csv "$(AIRPORTS_CSV)"
