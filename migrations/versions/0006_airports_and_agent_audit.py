from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "0006_airports_and_agent_audit"
down_revision = "0005_telegram_update_dedupe"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "airports",
        sa.Column("iata_code", sa.String(length=3), primary_key=True),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("municipality", sa.String(length=160), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("airport_type", sa.String(length=40), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("keywords", sa.String(length=500), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_airports_country_code", "airports", ["country_code"])
    op.create_index("ix_airports_airport_type", "airports", ["airport_type"])

    op.create_table(
        "airport_import_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("source_path", sa.String(length=500), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rows_seen", sa.Integer(), nullable=False),
        sa.Column("rows_imported", sa.Integer(), nullable=False),
    )
    op.create_index("ix_airport_import_runs_source", "airport_import_runs", ["source"])

    op.create_table(
        "agent_audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("tool_name", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("policy_decision", sa.String(length=120), nullable=False),
        sa.Column("related_id", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_audit_events_household_id", "agent_audit_events", ["household_id"])
    op.create_index("ix_agent_audit_events_user_id", "agent_audit_events", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_audit_events_user_id", table_name="agent_audit_events")
    op.drop_index("ix_agent_audit_events_household_id", table_name="agent_audit_events")
    op.drop_table("agent_audit_events")
    op.drop_index("ix_airport_import_runs_source", table_name="airport_import_runs")
    op.drop_table("airport_import_runs")
    op.drop_index("ix_airports_airport_type", table_name="airports")
    op.drop_index("ix_airports_country_code", table_name="airports")
    op.drop_table("airports")
