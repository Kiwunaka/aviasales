from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "0004_live_observation_idempotency"
down_revision = "0003_live_observations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "live_observation_idempotency",
        sa.Column("dedupe_key", sa.String(length=300), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("idempotency_key", sa.String(length=240), nullable=False),
        sa.Column("observation_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_live_observation_idempotency_user_id",
        "live_observation_idempotency",
        ["user_id"],
    )
    op.create_index(
        "ix_live_observation_idempotency_observation_id",
        "live_observation_idempotency",
        ["observation_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_live_observation_idempotency_observation_id",
        table_name="live_observation_idempotency",
    )
    op.drop_index(
        "ix_live_observation_idempotency_user_id",
        table_name="live_observation_idempotency",
    )
    op.drop_table("live_observation_idempotency")
