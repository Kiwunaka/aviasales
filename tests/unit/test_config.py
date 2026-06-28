from __future__ import annotations

from pathlib import Path

from flight_hunter.config import AppSettings, load_env_file


def test_settings_detects_travelpayouts_credentials_without_exposing_value(
    monkeypatch,
) -> None:
    monkeypatch.setenv("AVIASALES_DATA_ENABLED", "true")
    monkeypatch.setenv("TRAVELPAYOUTS_API_TOKEN", "secret-value")

    settings = AppSettings.from_env()

    assert settings.aviasales_data_enabled
    assert settings.travelpayouts_api_token == "secret-value"
    assert settings.aviasales_data_credentials_present


def test_load_env_file_sets_missing_values_without_overriding_existing_env(
    tmp_path: Path,
    monkeypatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "AVIASALES_DATA_ENABLED=true\n"
        "TRAVELPAYOUTS_API_TOKEN=file-secret\n"
        "AVIASALES_DATA_DEFAULT_MARKET=pl\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TRAVELPAYOUTS_API_TOKEN", "existing-secret")

    load_env_file(env_file)
    settings = AppSettings.from_env()

    assert settings.aviasales_data_enabled
    assert settings.travelpayouts_api_token == "existing-secret"
    assert settings.aviasales_data_default_market == "pl"
