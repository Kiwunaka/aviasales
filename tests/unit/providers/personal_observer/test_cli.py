from __future__ import annotations

import json
from pathlib import Path

import pytest

from flight_hunter.providers.personal_observer.cli import main

FIXTURE = Path("tests/fixtures/browser/tutu/search_result_sanitized.html")


def test_observe_cli_prints_sanitized_fixture_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PERSONAL_OBSERVER_PROFILE_ROOT", str(tmp_path / "profiles"))
    monkeypatch.setenv("PERSONAL_OBSERVER_ALLOWED_HOSTS", "www.tutu.ru,tutu.ru,avia.tutu.ru")
    monkeypatch.setattr(
        "sys.argv",
        [
            "flight-hunter-observe",
            "--source",
            "tutu",
            "--origin",
            "MOW",
            "--destination",
            "IST",
            "--depart",
            "2026-09-10",
            "--return-date",
            "2026-09-20",
            "--fixture-html",
            str(FIXTURE),
        ],
    )

    main()

    body = json.loads(capsys.readouterr().out)
    assert body["source_id"] == "tutu"
    assert body["confidence"] == "medium"
    assert body["offers"][0]["amount_minor"] == 1_842_000
    assert "html" not in body


def test_observe_cli_returns_typed_error_without_fixture_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PERSONAL_OBSERVER_ENABLED", "false")
    monkeypatch.setenv("PERSONAL_OBSERVER_PROFILE_ROOT", str(tmp_path / "profiles"))
    monkeypatch.setenv("PERSONAL_OBSERVER_ALLOWED_HOSTS", "www.tutu.ru,tutu.ru,avia.tutu.ru")
    monkeypatch.setattr(
        "sys.argv",
        [
            "flight-hunter-observe",
            "--source",
            "tutu",
            "--origin",
            "MOW",
            "--destination",
            "IST",
            "--depart",
            "2026-09-10",
            "--return-date",
            "2026-09-20",
            "--interactive",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 2
    body = json.loads(capsys.readouterr().out)
    assert body["code"] == "observer_disabled"
