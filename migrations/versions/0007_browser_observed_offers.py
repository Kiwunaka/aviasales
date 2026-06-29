from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "0007_browser_observed_offers"
down_revision = "0006_airports_and_agent_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "browser_observed_offers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("search_id", sa.String(length=160), nullable=False),
        sa.Column("source_id", sa.String(length=80), nullable=False),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("provider_offer_id", sa.String(length=160), nullable=False),
        sa.Column("origin", sa.String(length=3), nullable=False),
        sa.Column("destination", sa.String(length=3), nullable=False),
        sa.Column("departure_date", sa.String(length=10), nullable=True),
        sa.Column("return_date", sa.String(length=10), nullable=True),
        sa.Column("amount_minor", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("passengers", sa.Integer(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("final_url", sa.String(length=1000), nullable=False),
        sa.Column("display_url", sa.String(length=240), nullable=False),
        sa.Column("freshness", sa.String(length=40), nullable=False),
        sa.Column("confidence", sa.String(length=20), nullable=False),
        sa.Column("parser_version", sa.String(length=120), nullable=False),
        sa.Column("parser_warnings_json", sa.String(length=1000), nullable=False),
        sa.Column("airline_name", sa.String(length=160), nullable=True),
        sa.Column("airline_iata", sa.String(length=3), nullable=True),
        sa.Column("flight_number", sa.String(length=40), nullable=True),
        sa.Column("departure_time_local", sa.String(length=40), nullable=True),
        sa.Column("arrival_time_local", sa.String(length=40), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("stops", sa.Integer(), nullable=True),
        sa.Column("baggage_summary", sa.String(length=240), nullable=True),
        sa.Column("seller_name", sa.String(length=160), nullable=True),
        sa.Column("requires_external_confirmation", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_browser_observed_offers_household_id",
        "browser_observed_offers",
        ["household_id"],
    )
    op.create_index("ix_browser_observed_offers_user_id", "browser_observed_offers", ["user_id"])
    op.create_index(
        "ix_browser_observed_offers_search_id",
        "browser_observed_offers",
        ["search_id"],
    )
    op.create_index(
        "ix_browser_observed_offers_source_id",
        "browser_observed_offers",
        ["source_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_browser_observed_offers_source_id", table_name="browser_observed_offers")
    op.drop_index("ix_browser_observed_offers_search_id", table_name="browser_observed_offers")
    op.drop_index("ix_browser_observed_offers_user_id", table_name="browser_observed_offers")
    op.drop_index("ix_browser_observed_offers_household_id", table_name="browser_observed_offers")
    op.drop_table("browser_observed_offers")
