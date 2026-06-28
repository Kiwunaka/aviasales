from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from flight_hunter.domain.money import Money
from flight_hunter.domain.observation import (
    BrowserSource,
    LiveObservation,
    ObservationStatus,
    ObserverCapability,
    PermissionAttestation,
    PermissionStatus,
)
from flight_hunter.domain.offers import FlightOffer, Freshness

NOW = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)


def attestation(**overrides: object) -> PermissionAttestation:
    values: dict[str, object] = {
        "attestation_id": "att_demo",
        "source_id": "demo_browser",
        "allowed_domains": ("example.test",),
        "allowed_capabilities": (
            ObserverCapability.PUBLIC_NAVIGATION,
            ObserverCapability.PUBLIC_DOM_READ,
        ),
        "document_ref": "docs/provider-contracts/demo-browser.md",
        "document_hash": "sha256:abc",
        "valid_from": NOW - timedelta(days=1),
        "valid_until": NOW + timedelta(days=30),
        "terms_verified_at": NOW,
        "approved_by": "flight-hunter",
        "revoked_at": None,
    }
    values.update(overrides)
    return PermissionAttestation(**values)


def test_permission_attestation_reports_active_expired_and_revoked_states() -> None:
    assert attestation().status_at(NOW) == PermissionStatus.ACTIVE
    assert attestation(valid_until=NOW - timedelta(seconds=1)).status_at(NOW) == (
        PermissionStatus.EXPIRED
    )
    assert attestation(revoked_at=NOW - timedelta(minutes=1)).status_at(NOW) == (
        PermissionStatus.REVOKED
    )


def test_permission_attestation_rejects_prohibited_browser_capabilities() -> None:
    with pytest.raises(ValueError, match="prohibited capability"):
        attestation(allowed_capabilities=("challenge_bypass",))


def test_browser_source_never_allows_background_execution() -> None:
    source = BrowserSource(
        source_id="demo_browser",
        display_name="Demo browser observer",
        enabled=True,
        supported_routes=("WAW-BCN",),
        current_health="healthy",
        attestation=attestation(),
    )

    assert source.permission_status(NOW) == PermissionStatus.ACTIVE
    assert source.background_allowed is False


def test_live_observation_uses_typed_status_and_live_observed_offer_label() -> None:
    offer = FlightOffer(
        provider_id="demo_browser",
        provider_offer_id="live-demo-1",
        origin="WAW",
        destination="BCN",
        departure_date="2026-10-12",
        return_date="2026-10-19",
        total_price=Money(minor_units=151200, currency="RUB"),
        passengers=2,
        observed_at=NOW,
        freshness=Freshness.LIVE_OBSERVED,
        requires_live_confirmation=True,
        baggage_summary=None,
    )

    observation = LiveObservation(
        observation_id=UUID("33333333-3333-3333-3333-333333333333"),
        grant_id=UUID("22222222-2222-2222-2222-222222222222"),
        user_id=UUID("11111111-1111-1111-1111-111111111111"),
        source_id="demo_browser",
        search_intent_hash="sha256:abc",
        status=ObservationStatus.SUCCEEDED,
        created_at=NOW,
        started_at=NOW,
        completed_at=NOW,
        expires_at=NOW + timedelta(minutes=15),
        offers=(offer,),
        error_code=None,
        error_message=None,
    )

    assert observation.status == ObservationStatus.SUCCEEDED
    assert observation.offers[0].freshness == Freshness.LIVE_OBSERVED
