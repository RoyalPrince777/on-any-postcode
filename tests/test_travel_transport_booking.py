from __future__ import annotations

import pytest
from flask import Flask

from mission_control import global_transport_views, travel_transport_booking


def _app():
    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(global_transport_views.bp)
    return app


def test_travel_transport_modes_are_explicit():
    current = travel_transport_booking.status()
    assert current["modes"] == ["bus", "ferry", "flight", "rail"]
    assert current["quote_ready"] is True
    assert current["hold_ready"] is True
    assert current["reservation_ready"] is True
    assert current["ticket_issuance_software_ready"] is True
    assert current["raw_licence_evidence_required_in_chat"] is False
    assert current["raw_licence_evidence_exposed"] is False


def test_quote_reuses_direct_transport_inventory(monkeypatch):
    monkeypatch.setattr(
        travel_transport_booking.travel_marketplace,
        "quote_direct",
        lambda payload: {
            "category": "transport",
            "listing_id": "listing-1",
            "total_price_minor": 5500,
            "currency": "GBP",
        },
    )
    result = travel_transport_booking.quote(
        {
            "mode": "rail",
            "listing_id": "listing-1",
            "starts_at": "2026-10-04T10:00:00+00:00",
            "ends_at": "2026-10-04T11:00:00+00:00",
        }
    )
    assert result["mode"] == "rail"
    assert result["journey_segment_type"] == "rail"
    assert result["reservation_confirmed"] is False
    assert result["ticket_issued"] is False


def test_quote_rejects_non_transport_inventory(monkeypatch):
    monkeypatch.setattr(
        travel_transport_booking.travel_marketplace,
        "quote_direct",
        lambda payload: {"category": "stay"},
    )
    with pytest.raises(ValueError, match="transport_listing_required"):
        travel_transport_booking.quote({"mode": "bus"})


def test_invalid_travel_mode_fails_closed():
    with pytest.raises(ValueError, match="invalid_travel_mode"):
        travel_transport_booking.quote({"mode": "teleport"})


def test_ticket_issuance_stays_locked_without_verified_gate(monkeypatch):
    monkeypatch.setattr(
        travel_transport_booking.transport_execution_evidence,
        "status",
        lambda: {
            "areas": {
                "ticket_issuance": {
                    "live_execution_authorised": False,
                    "verified": ["issuer_authority"],
                    "missing": [
                        "inventory_or_entitlement_proof",
                        "issued_ticket_receipt",
                    ],
                }
            }
        },
    )
    with pytest.raises(PermissionError, match="ticket_issuance_evidence_incomplete"):
        travel_transport_booking.issue_ticket(
            owner_identity_id="11111111-1111-4111-8111-111111111111",
            reservation_id="22222222-2222-4222-8222-222222222222",
            mode="flight",
            issued_ticket_receipt_hash="a" * 64,
        )


def test_travel_routes_are_registered():
    rules = {rule.rule for rule in _app().url_map.iter_rules()}
    assert "/transport/travel/status" in rules
    assert "/transport/travel/quote" in rules
    assert "/transport/travel/hold" in rules
    assert "/transport/travel/reservations" in rules
    assert "/transport/travel/reservations/confirm" in rules
    assert "/transport/travel/reservations/<reservation_id>/ticket" in rules


def test_travel_status_is_no_store(monkeypatch):
    monkeypatch.setattr(
        travel_transport_booking,
        "status",
        lambda: {
            "component": "OAP Journey Travel Booking",
            "modes": ["bus", "ferry", "flight", "rail"],
        },
    )
    response = _app().test_client().get("/transport/travel/status")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store, private"
