from __future__ import annotations

import argparse
import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class BackupResult:
    ok: bool
    code: str
    path: Path | None


def create_sqlite_backup(
    *,
    database_path: Path,
    backup_dir: Path,
    clock: Callable[[], datetime] | None = None,
) -> BackupResult:
    if not database_path.exists():
        return BackupResult(ok=False, code="database_missing", path=None)

    now = clock or (lambda: datetime.now(UTC))
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"flight_hunter_{_timestamp(now())}.db"
    shutil.copy2(database_path, backup_path)
    return BackupResult(ok=True, code="ok", path=backup_path)


def restore_sqlite_backup(
    *,
    database_path: Path,
    backup_path: Path,
    clock: Callable[[], datetime] | None = None,
) -> BackupResult:
    if not backup_path.exists():
        return BackupResult(ok=False, code="backup_missing", path=None)

    now = clock or (lambda: datetime.now(UTC))
    previous_path: Path | None = None
    if database_path.exists():
        previous_path = database_path.with_name(
            f"{database_path.stem}.before-restore-{_timestamp(now())}{database_path.suffix}"
        )
        shutil.copy2(database_path, previous_path)

    database_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_path, database_path)
    return BackupResult(ok=True, code="ok", path=previous_path)


def backup_main() -> int:
    parser = argparse.ArgumentParser(description="Back up local Flight Hunter SQLite database.")
    parser.add_argument("--database", default="flight_hunter_dev.db")
    parser.add_argument("--backup-dir", default="backups")
    args = parser.parse_args()

    result = create_sqlite_backup(
        database_path=Path(args.database),
        backup_dir=Path(args.backup_dir),
    )
    print(_result_json(result))
    return 0 if result.ok else 1


def restore_main() -> int:
    parser = argparse.ArgumentParser(description="Restore local Flight Hunter SQLite database.")
    parser.add_argument("backup")
    parser.add_argument("--database", default="flight_hunter_dev.db")
    args = parser.parse_args()

    result = restore_sqlite_backup(
        database_path=Path(args.database),
        backup_path=Path(args.backup),
    )
    print(_result_json(result))
    return 0 if result.ok else 1


def _timestamp(value: datetime) -> str:
    normalized = value.astimezone(UTC)
    return normalized.strftime("%Y%m%dT%H%M%SZ")


def _result_json(result: BackupResult) -> str:
    return json.dumps(
        {
            "ok": result.ok,
            "code": result.code,
            "path": str(result.path) if result.path is not None else None,
        },
        ensure_ascii=False,
        indent=2,
    )
