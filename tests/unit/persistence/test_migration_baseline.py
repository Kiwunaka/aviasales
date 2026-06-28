from __future__ import annotations

import importlib.util
from pathlib import Path


def test_migrations_have_upgrade_and_downgrade() -> None:
    migration_paths = sorted(Path("migrations/versions").glob("*.py"))

    assert migration_paths

    for migration_path in migration_paths:
        spec = importlib.util.spec_from_file_location(migration_path.stem, migration_path)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert callable(module.upgrade)
        assert callable(module.downgrade)
