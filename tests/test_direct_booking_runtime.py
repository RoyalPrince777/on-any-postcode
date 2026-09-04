from __future__ import annotations

from mission_control import travel_marketplace, travel_supply_views, web_security


def _csrf_headers(client):
    token = "direct-booking-csrf-token-12345678901234567890"
    with client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token
    return {"X-OAP-CSRF": token}


def _direct_template() -> str:
    with open("mission_control/templates/travel_direct.html", encoding="utf-8") as handle:
        return handle.read()


def _control_template() -> str:
    with open(
        "mission_control/templates/travel_supply_control.html", encoding="utf-8"
    ) as handle:
        return handle.read()


def test_direct_marketplace_wrappers_bind_identity_and_human_gates(monkeypatch):
    calls = {}

    def fake_quote(**kwargs):
        calls["quote"] = kwargs
        return {"source": "oap_direct"}

    def fake_hold(**kwargs):
        calls["hold"] = kwargs
        return {"state": "HELD"}

    def fake_reservation(**kwargs):
        calls["reservation"] = kwargs
        return {"state": "PENDING_SUPPLIER_CONFIRMATION"}

    def fake_confirm(**kwargs):
        calls["confirm"] = kwargs
        return {"state": "CONFIRMED"}

    monkeypatch.setattr(travel_marketplace._STORE, "quote", fake_quote)
    monkeypatch.setattr(travel_marketplace._STORE, "create_hold", fake_hold)
    monkeypatch.setattr(travel_marketplace._STORE, "create_reservation", fake_reservation)
    monkeypatch.setattr(travel_marketplace._STORE, "confirm_reservation", fake_confirm)

    payload = {
        "listing_id": "listing-1",
        "starts_at": "2026-09-05T10:00:00+00:00",
        "ends_at": "2026-09-05T12:00:00+00:00",
        "quantity": 2,
        "idempotency_key": "hold-1",
        "buyer_identity_id": "payload-must-not-control-identity",
    }
    travel_marketplace.quote_direct(payload)
    travel_marketplace.create_buyer_hold(payload, buyer_identity_id="buyer-session")
    travel_marketplace.create_buyer_reservation(
        {"hold_id": "hold-1", "human_confirmed": True},
        buyer_identity_id="buyer-session",
    )
    travel_marketplace.confirm_supplier_reservation(
        {
            "reservation_id": "reservation-1",
            "supplier_confirmation_reference": "SUPPLIER-REF-1",
            "supplier_confirmed": True,
        },
        owner_identity_id="supplier-owner-session",
    )

    assert calls["quote"]["quantity"] == 2
    assert calls["hold"]["buyer_identity_id"] == "buyer-session"
    assert calls["hold"]["hold_minutes"] == 15
    assert calls["reservation"]["buyer_identity_id"] == "buyer-session"
    assert calls["reservation"]["human_confirmed"] is True
    assert calls["confirm"]["owner_identity_id"] == "supplier-owner-session"
    assert calls["confirm"]["supplier_confirmed"] is True


def test_hold_and_reservation_routes_require_authentication(anonymous_client):
    assert anonymous_client.post("/travel/direct/api/hold", json={}).status_code == 401
    assert (
        anonymous_client.post("/travel/direct/api/reservations", json={}).status_code
        == 401
    )


def test_quote_is_read_only_and_does_not_require_authentication(
    anonymous_client, monkeypatch
):
    monkeypatch.setattr(
        travel_supply_views.travel_marketplace,
        "quote_direct",
        lambda payload: {
            "source": "oap_direct",
            "listing_id": payload["listing_id"],
            "total_price_minor": 2500,
            "currency": "GBP",
        },
    )
    response = anonymous_client.post(
        "/travel/direct/api/quote",
        json={"listing_id": "listing-live"},
    )
    assert response.status_code == 200
    assert response.get_json()["total_price_minor"] == 2500


def test_authenticated_hold_requires_csrf(client):
    response = client.post("/travel/direct/api/hold", json={})
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"


def test_authenticated_hold_uses_verified_session_identity(client, monkeypatch):
    captured = {}

    def fake_hold(payload, *, buyer_identity_id):
        captured["payload"] = payload
        captured["buyer_identity_id"] = buyer_identity_id
        return {
            "hold_id": "22222222-2222-4222-8222-222222222222",
            "state": "HELD",
            "expires_at": "2026-09-05T10:15:00+00:00",
            "payment_captured": False,
        }

    monkeypatch.setattr(
        travel_supply_views.travel_marketplace,
        "create_buyer_hold",
        fake_hold,
    )
    response = client.post(
        "/travel/direct/api/hold",
        json={"buyer_identity_id": "attacker-supplied-id", "listing_id": "listing-live"},
        headers=_csrf_headers(client),
    )
    assert response.status_code == 200
    assert captured["buyer_identity_id"] == "11111111-1111-4111-8111-111111111111"
    assert response.get_json()["payment_captured"] is False


def test_reservation_requires_explicit_human_confirmation(client, monkeypatch):
    captured = {}

    def fake_reservation(payload, *, buyer_identity_id):
        captured["payload"] = payload
        captured["buyer_identity_id"] = buyer_identity_id
        if payload.get("human_confirmed") is not True:
            raise PermissionError("human_confirmation_required")
        return {
            "state": "PENDING_SUPPLIER_CONFIRMATION",
            "payment_captured": False,
            "pass_issued": False,
        }

    monkeypatch.setattr(
        travel_supply_views.travel_marketplace,
        "create_buyer_reservation",
        fake_reservation,
    )
    headers = _csrf_headers(client)
    blocked = client.post(
        "/travel/direct/api/reservations",
        json={"hold_id": "hold-1", "human_confirmed": False},
        headers=headers,
    )
    assert blocked.status_code == 403

    allowed = client.post(
        "/travel/direct/api/reservations",
        json={"hold_id": "hold-1", "human_confirmed": True},
        headers=headers,
    )
    assert allowed.status_code == 200
    assert allowed.get_json()["state"] == "PENDING_SUPPLIER_CONFIRMATION"
    assert allowed.get_json()["payment_captured"] is False


def test_supplier_confirmation_is_founder_and_csrf_gated(client, monkeypatch):
    without_csrf = client.post(
        "/mission/supply/reservations/confirm",
        json={"reservation_id": "reservation-1"},
    )
    assert without_csrf.status_code == 403

    captured = {}

    def fake_confirm(payload, *, owner_identity_id):
        captured["payload"] = payload
        captured["owner_identity_id"] = owner_identity_id
        return {
            "state": "CONFIRMED",
            "reservation_confirmed": True,
            "payment_captured": False,
            "pass_issued": False,
            "commission_settled": False,
        }

    monkeypatch.setattr(
        travel_supply_views.travel_marketplace,
        "confirm_supplier_reservation",
        fake_confirm,
    )
    response = client.post(
        "/mission/supply/reservations/confirm",
        json={
            "reservation_id": "reservation-1",
            "supplier_confirmation_reference": "SUPPLIER-REF-1",
            "supplier_confirmed": True,
        },
        headers=_csrf_headers(client),
    )
    assert response.status_code == 200
    assert captured["owner_identity_id"] == "11111111-1111-4111-8111-111111111111"
    assert response.get_json()["payment_captured"] is False
    assert response.get_json()["commission_settled"] is False


def test_public_direct_ui_has_real_bounded_booking_controls():
    page = _direct_template()
    assert "Check & hold" in page
    assert "Human Confirm · Create reservation" in page
    assert "/travel/direct/api/quote" in page
    assert "/travel/direct/api/hold" in page
    assert "/travel/direct/api/reservations" in page
    assert "15-minute capacity hold" in page
    assert "No payment will be taken" in page


def test_founder_booking_control_can_confirm_real_supplier_reservation():
    page = _control_template()
    assert 'data-endpoint="/mission/supply/reservations/confirm"' in page
    assert 'data-supplier-confirm="1"' in page
    assert "Supplier Confirm · Reservation" in page
    assert "PENDING_SUPPLIER_CONFIRMATION" in page
    assert (
        "Payment capture, OAP Pass issuance and commission settlement remain "
        "separately governed"
        in page
    )
