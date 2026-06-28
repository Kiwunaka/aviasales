from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "0003_live_observations"
down_revision = "0002_price_history_and_alert_dedupe"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_action_grants",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("provider_id", sa.String(length=80), nullable=False),
        sa.Column("action_type", sa.String(length=80), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=160), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_user_action_grants_user_id", "user_action_grants", ["user_id"])
    op.create_index("ix_user_action_grants_provider_id", "user_action_grants", ["provider_id"])

    op.create_table(
        "live_observations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("grant_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=80), nullable=False),
        sa.Column("search_intent_hash", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
    )
    op.create_index("ix_live_observations_grant_id", "live_observations", ["grant_id"])
    op.create_index("ix_live_observations_user_id", "live_observations", ["user_id"])
    op.create_index("ix_live_observations_source_id", "live_observations", ["source_id"])

    op.create_table(
        "live_observation_offers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("observation_id", sa.String(length=36), nullable=False),
        sa.Column("provider_id", sa.String(length=80), nullable=False),
        sa.Column("provider_offer_id", sa.String(length=160), nullable=False),
        sa.Column("origin", sa.String(length=3), nullable=False),
        sa.Column("destination", sa.String(length=3), nullable=False),
        sa.Column("departure_date", sa.String(length=10), nullable=False),
        sa.Column("return_date", sa.String(length=10), nullable=True),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("passengers", sa.Integer(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("freshness", sa.String(length=30), nullable=False),
        sa.Column("requires_live_confirmation", sa.Boolean(), nullable=False),
        sa.Column("baggage_summary", sa.String(length=240), nullable=True),
    )
    op.create_index(
        "ix_live_observation_offers_observation_id",
        "live_observation_offers",
        ["observation_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_live_observation_offers_observation_id",
        table_name="live_observation_offers",
    )
    op.drop_table("live_observation_offers")
    op.drop_index("ix_live_observations_source_id", table_name="live_observations")
    op.drop_index("ix_live_observations_user_id", table_name="live_observations")
    op.drop_index("ix_live_observations_grant_id", table_name="live_observations")
    op.drop_table("live_observations")
    op.drop_index("ix_user_action_grants_provider_id", table_name="user_action_grants")
    op.drop_index("ix_user_action_grants_user_id", table_name="user_action_grants")
    op.drop_table("user_action_grants")
