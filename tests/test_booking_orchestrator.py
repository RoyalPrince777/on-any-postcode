from datetime import UTC, datetime

import pytest

from oap.smi import booking_orchestrator, travel_agency


def _offer(**overrides):
    payload = {
        "provider_id": "booking_com",
        "category": "stay",
        "source_offer_id": "hotel-123-rate-1",
        "title": "Example Stay",
        "place_label": "London, United Kingdom",
        "availability_state": "available",
        "observed_at": "2026-09-04T11:00:00+00:00",
        "source_url": "https://www.booking.com/hotel/gb/example.html",
        "currency": "GBP",
        "total_price": 240.0,
        "price_basis": "2 nights total",
        "expires_at": "2026-09-04T11:30:00+00:00",
    }
    payload.update(overrides)
    return payload


def test_oap_booking_core_prepares_intent_but_does_not_book():
    intent = booking_orchestrator.prepare_booking_intent(
        _offer(),
        now=datetime(2026, 9, 4, 11, 5, tzinfo=UTC),
    )

    assert intent.intent_id.startswith("oap-book-")
    assert intent.state == "awaiting_human_confirmation"
    assert intent.human_confirmation_required is True
    assert intent.human_confirmed is False
    assert intent.booking_execution_authorized is False
    assert intent.payment_execution_authorized is False
    assert intent.pass_issuance_authorized is False


def test_human_approval_creates_handoff_not_false_confirmation():
    intent = booking_orchestrator.prepare_booking_intent(
        _offer(),
        now=datetime(2026, 9, 4, 11, 5, tzinfo=UTC),
    )
    approved = booking_orchestrator.confirm_booking_intent(intent, human_approved=True)
    handoff = booking_orchestrator.booking_handoff(approved)

    assert approved.state == "handoff_ready"
    assert approved.human_confirmed is True
    assert handoff["state"] == "external_supplier_handoff"
    assert handoff["reservation_confirmed"] is False
    assert handoff["payment_captured"] is False
    assert handoff["pass_issued"] is False
    assert handoff["provider_authority"] is False
    assert handoff["human_authority_final"] is True


def test_declined_booking_intent_cannot_handoff():
    intent = booking_orchestrator.prepare_booking_intent(
        _offer(),
        now=datetime(2026, 9, 4, 11, 5, tzinfo=UTC),
    )
    declined = booking_orchestrator.confirm_booking_intent(intent, human_approved=False)

    assert declined.state == "declined"
    with pytest.raises(ValueError, match="booking_handoff_not_ready"):
        booking_orchestrator.booking_handoff(declined)


def test_stale_or_expired_offer_cannot_create_booking_intent():
    with pytest.raises(ValueError, match="offer_evidence_stale_or_expired"):
        booking_orchestrator.prepare_booking_intent(
            _offer(expires_at="2026-09-04T11:04:00+00:00"),
            now=datetime(2026, 9, 4, 11, 5, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="offer_evidence_stale_or_expired"):
        booking_orchestrator.prepare_booking_intent(
            _offer(observed_at="2026-09-04T10:30:00+00:00", expires_at=None),
            now=datetime(2026, 9, 4, 11, 5, tzinfo=UTC),
        )


def test_unavailable_offer_cannot_create_booking_intent():
    with pytest.raises(ValueError, match="offer_not_bookable"):
        booking_orchestrator.prepare_booking_intent(
            _offer(availability_state="unavailable"),
            now=datetime(2026, 9, 4, 11, 5, tzinfo=UTC),
        )


def test_oap_owns_booking_experience_not_external_inventory(monkeypatch):
    for key in tuple(__import__("os").environ):
        if key.startswith("OAP_SUPPLY_BOOKING_COM_"):
            monkeypatch.delenv(key, raising=False)

    booking = booking_orchestrator.status()
    agency = travel_agency.status()

    assert booking["first_party_booking_orchestration_ready"] is True
    assert booking["owns_booking_experience"] is True
    assert booking["owns_supplier_inventory"] is False
    assert booking["direct_booking_execution_ready"] is False
    assert booking["payment_execution_ready"] is False
    assert booking["creates_intelligence_worlds"] is False
    assert booking["creates_agents"] is False
    assert booking["creates_brain"] is False
    assert booking["external_provider_authority"] is False
    assert agency["oap_booking_core_ready"] is True
    assert agency["oap_owns_booking_experience"] is True
    assert agency["oap_owns_supplier_inventory"] is False
    assert agency["booking_transactions_live"] is False
    assert agency["payment_transactions_live"] is False
