# ADR 0012: Local SQLite Backup Restore

Date: 2026-06-23

## Status

Accepted.

## Context

The full product will use production-grade database backups. Before that, the local demo SQLite database still needs a safe backup/restore command so beginner usage does not depend on manual file copying.

## Decision

- Add `flight-hunter-backup` for local SQLite backups.
- Add `flight-hunter-restore` for local SQLite restores.
- Save the previous database copy before restore.
- Keep backup files out of the repository via `.gitignore`.
- Treat PostgreSQL backup/restore as a later production operations slice.

## Consequences

- Local demo data can be backed up and restored predictably.
- Restore is less destructive because the previous database is preserved.
- Production PostgreSQL backup runbooks remain pending.
