from __future__ import annotations

from datetime import UTC, datetime

from flight_hunter.application.provider_registry import ProviderRegistry
from flight_hunter.config import AppSettings

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)


def test_registry_enables_aviasales_data_when_flag_and_credentials_exist() -> None:
    registry = ProviderRegistry.default(
        clock=lambda: NOW,
        settings=AppSettings(
            database_url="sqlite+aiosqlite:///:memory:",
            aviasales_data_enabled=True,
            travelpayouts_api_token="secret-value",
            aviasales_data_default_market="pl",
            aviasales_data_internal_rpm=30,
            telegram_enabled=False,
            telegram_webhook_secret=None,
        ),
    )

    providers = {status.provider_id: status for status in registry.statuses()}

    assert providers["aviasales_data"].enabled
    assert providers["aviasales_data"].credentials_present
    assert providers["aviasales_data"].blocked_reasons == ()
    assert "secret-value" not in str(providers["aviasales_data"])
