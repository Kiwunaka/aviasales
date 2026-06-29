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


def test_settings_parse_personal_observer_and_clickout_lists(monkeypatch) -> None:
    monkeypatch.setenv("PERSONAL_OBSERVER_ALLOWED_HOSTS", "travel.yandex.ru,www.tutu.ru")
    monkeypatch.setenv("RU_AGGREGATORS_ENABLED", "tutu")
    monkeypatch.setenv("CARRIER_LINKS_ENABLED", "s7,pobeda")

    settings = AppSettings.from_env()

    assert settings.personal_observer_allowed_hosts == ("travel.yandex.ru", "www.tutu.ru")
    assert settings.ru_aggregators_enabled == ("tutu",)
    assert settings.carrier_links_enabled == ("s7", "pobeda")
    assert settings.ru_clickout_enabled_source_ids == ("tutu", "s7", "pobeda")
