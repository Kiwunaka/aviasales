from __future__ import annotations

from datetime import UTC, datetime

from flight_hunter.ops.backup import (
    BackupResult,
    create_sqlite_backup,
    restore_sqlite_backup,
)

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)


def test_backup_reports_missing_database_without_creating_file(tmp_path) -> None:
    result = create_sqlite_backup(
        database_path=tmp_path / "missing.db",
        backup_dir=tmp_path / "backups",
        clock=lambda: NOW,
    )

    assert result == BackupResult(ok=False, code="database_missing", path=None)
    assert not (tmp_path / "backups").exists()


def test_backup_copies_sqlite_database_to_timestamped_file(tmp_path) -> None:
    database_path = tmp_path / "flight_hunter_dev.db"
    database_path.write_bytes(b"sqlite-data")

    result = create_sqlite_backup(
        database_path=database_path,
        backup_dir=tmp_path / "backups",
        clock=lambda: NOW,
    )

    assert result.ok is True
    assert result.code == "ok"
    assert result.path is not None
    assert result.path.name == "flight_hunter_20260623T120000Z.db"
    assert result.path.read_bytes() == b"sqlite-data"


def test_restore_replaces_database_from_backup_and_saves_previous_copy(tmp_path) -> None:
    database_path = tmp_path / "flight_hunter_dev.db"
    backup_path = tmp_path / "backup.db"
    database_path.write_bytes(b"old")
    backup_path.write_bytes(b"restored")

    result = restore_sqlite_backup(
        database_path=database_path,
        backup_path=backup_path,
        clock=lambda: NOW,
    )

    assert result.ok is True
    assert result.code == "ok"
    assert database_path.read_bytes() == b"restored"
    assert (
        tmp_path / "flight_hunter_dev.before-restore-20260623T120000Z.db"
    ).read_bytes() == b"old"
