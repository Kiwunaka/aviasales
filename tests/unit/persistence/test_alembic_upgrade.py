from __future__ import annotations

import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config


def test_alembic_upgrade_head_creates_current_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "flight_hunter_test.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{db_path.as_posix()}")

    command.upgrade(config, "head")

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "select name from sqlite_master where type = 'table'"
            ).fetchall()
        }

    assert {
        "watches",
        "price_snapshots",
        "alert_dedupe_entries",
        "user_action_grants",
        "live_observations",
        "live_observation_offers",
        "live_observation_idempotency",
        "telegram_update_dedupe",
    }.issubset(tables)
