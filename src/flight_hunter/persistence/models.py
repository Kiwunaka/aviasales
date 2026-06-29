from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, MetaData, String, Table
from sqlalchemy.orm import registry

metadata = MetaData()
mapper_registry = registry(metadata=metadata)


watches_table = Table(
    "watches",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("household_id", String(36), nullable=False, index=True),
    Column("owner_user_id", String(36), nullable=False),
    Column("origin", String(3), nullable=False),
    Column("destination", String(3), nullable=False),
    Column("departure_date", String(10), nullable=False),
    Column("return_date", String(10), nullable=True),
    Column("enabled", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


price_snapshots_table = Table(
    "price_snapshots",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("household_id", String(36), nullable=False, index=True),
    Column("watch_id", String(36), nullable=False, index=True),
    Column("provider_id", String(80), nullable=False),
    Column("itinerary_fingerprint", String(160), nullable=False),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Column("amount_minor", Integer, nullable=False),
    Column("currency", String(3), nullable=False),
    Column("freshness", String(20), nullable=False),
    Column("requires_live_confirmation", Boolean, nullable=False),
)


alert_dedupe_entries_table = Table(
    "alert_dedupe_entries",
    metadata,
    Column("dedupe_key", String(240), primary_key=True),
    Column("household_id", String(36), nullable=False, index=True),
    Column("watch_id", String(36), nullable=False, index=True),
    Column("itinerary_fingerprint", String(160), nullable=False),
    Column("reason", String(40), nullable=False),
    Column("sent_at", DateTime(timezone=True), nullable=False),
)


user_action_grants_table = Table(
    "user_action_grants",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("user_id", String(36), nullable=False, index=True),
    Column("provider_id", String(80), nullable=False, index=True),
    Column("action_type", String(80), nullable=False),
    Column("request_fingerprint", String(160), nullable=False),
    Column("issued_at", DateTime(timezone=True), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("source", String(40), nullable=False),
    Column("consumed_at", DateTime(timezone=True), nullable=True),
)


live_observations_table = Table(
    "live_observations",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("grant_id", String(36), nullable=False, index=True),
    Column("user_id", String(36), nullable=False, index=True),
    Column("source_id", String(80), nullable=False, index=True),
    Column("search_intent_hash", String(160), nullable=False),
    Column("status", String(40), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("error_code", String(80), nullable=True),
    Column("error_message", String(500), nullable=True),
)


live_observation_offers_table = Table(
    "live_observation_offers",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("observation_id", String(36), nullable=False, index=True),
    Column("provider_id", String(80), nullable=False),
    Column("provider_offer_id", String(160), nullable=False),
    Column("origin", String(3), nullable=False),
    Column("destination", String(3), nullable=False),
    Column("departure_date", String(10), nullable=False),
    Column("return_date", String(10), nullable=True),
    Column("amount_minor", Integer, nullable=False),
    Column("currency", String(3), nullable=False),
    Column("passengers", Integer, nullable=False),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Column("freshness", String(30), nullable=False),
    Column("requires_live_confirmation", Boolean, nullable=False),
    Column("baggage_summary", String(240), nullable=True),
)


live_observation_idempotency_table = Table(
    "live_observation_idempotency",
    metadata,
    Column("dedupe_key", String(300), primary_key=True),
    Column("user_id", String(36), nullable=False, index=True),
    Column("idempotency_key", String(240), nullable=False),
    Column("observation_id", String(36), nullable=False, index=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


browser_observed_offers_table = Table(
    "browser_observed_offers",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("household_id", String(36), nullable=False, index=True),
    Column("user_id", String(36), nullable=False, index=True),
    Column("search_id", String(160), nullable=False, index=True),
    Column("source_id", String(80), nullable=False, index=True),
    Column("source_name", String(120), nullable=False),
    Column("provider_offer_id", String(160), nullable=False),
    Column("origin", String(3), nullable=False),
    Column("destination", String(3), nullable=False),
    Column("departure_date", String(10), nullable=True),
    Column("return_date", String(10), nullable=True),
    Column("amount_minor", Integer, nullable=True),
    Column("currency", String(3), nullable=True),
    Column("passengers", Integer, nullable=False),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Column("final_url", String(1000), nullable=False),
    Column("display_url", String(240), nullable=False),
    Column("freshness", String(40), nullable=False),
    Column("confidence", String(20), nullable=False),
    Column("parser_version", String(120), nullable=False),
    Column("parser_warnings_json", String(1000), nullable=False),
    Column("airline_name", String(160), nullable=True),
    Column("airline_iata", String(3), nullable=True),
    Column("flight_number", String(40), nullable=True),
    Column("departure_time_local", String(40), nullable=True),
    Column("arrival_time_local", String(40), nullable=True),
    Column("duration_minutes", Integer, nullable=True),
    Column("stops", Integer, nullable=True),
    Column("baggage_summary", String(240), nullable=True),
    Column("seller_name", String(160), nullable=True),
    Column("requires_external_confirmation", Boolean, nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
)


telegram_update_dedupe_table = Table(
    "telegram_update_dedupe",
    metadata,
    Column("update_id", Integer, primary_key=True),
    Column("received_at", DateTime(timezone=True), nullable=False),
)


airports_table = Table(
    "airports",
    metadata,
    Column("iata_code", String(3), primary_key=True),
    Column("name", String(240), nullable=False),
    Column("municipality", String(160), nullable=False),
    Column("country_code", String(2), nullable=False, index=True),
    Column("latitude", Float, nullable=False),
    Column("longitude", Float, nullable=False),
    Column("airport_type", String(40), nullable=False, index=True),
    Column("active", Boolean, nullable=False),
    Column("keywords", String(500), nullable=False, default=""),
    Column("imported_at", DateTime(timezone=True), nullable=False),
)


airport_import_runs_table = Table(
    "airport_import_runs",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("source", String(80), nullable=False, index=True),
    Column("source_path", String(500), nullable=False),
    Column("imported_at", DateTime(timezone=True), nullable=False),
    Column("rows_seen", Integer, nullable=False),
    Column("rows_imported", Integer, nullable=False),
)


agent_audit_events_table = Table(
    "agent_audit_events",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("household_id", String(36), nullable=True, index=True),
    Column("user_id", String(36), nullable=True, index=True),
    Column("event_type", String(80), nullable=False),
    Column("tool_name", String(120), nullable=False),
    Column("summary", String(500), nullable=False),
    Column("policy_decision", String(120), nullable=False),
    Column("related_id", String(120), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)
