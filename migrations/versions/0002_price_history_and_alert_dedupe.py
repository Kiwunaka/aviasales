from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "0002_price_history_and_alert_dedupe"
down_revision = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "price_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("household_id", sa.String(length=36), nullable=False),
        sa.Column("watch_id", sa.String(length=36), nullable=False),
        sa.Column("provider_id", sa.String(length=80), nullable=False),
        sa.Column("itinerary_fingerprint", sa.String(length=160), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("freshness", sa.String(length=20), nullable=False),
        sa.Column("requires_live_confirmation", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_price_snapshots_household_id", "price_snapshots", ["household_id"])
    op.create_index("ix_price_snapshots_watch_id", "price_snapshots", ["watch_id"])

    op.create_table(
        "alert_dedupe_entries",
        sa.Column("dedupe_key", sa.String(length=240), primary_key=True),
        sa.Column("household_id", sa.String(length=36), nullable=False),
        sa.Column("watch_id", sa.String(length=36), nullable=False),
        sa.Column("itinerary_fingerprint", sa.String(length=160), nullable=False),
        sa.Column("reason", sa.String(length=40), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_alert_dedupe_entries_household_id",
        "alert_dedupe_entries",
        ["household_id"],
    )
    op.create_index("ix_alert_dedupe_entries_watch_id", "alert_dedupe_entries", ["watch_id"])


def downgrade() -> None:
    op.drop_index("ix_alert_dedupe_entries_watch_id", table_name="alert_dedupe_entries")
    op.drop_index("ix_alert_dedupe_entries_household_id", table_name="alert_dedupe_entries")
    op.drop_table("alert_dedupe_entries")
    op.drop_index("ix_price_snapshots_watch_id", table_name="price_snapshots")
    op.drop_index("ix_price_snapshots_household_id", table_name="price_snapshots")
    op.drop_table("price_snapshots")
