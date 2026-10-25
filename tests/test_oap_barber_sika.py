"""First-party barber supply and SIKA quote boundaries.

These tests enforce real certified DB sourcing; no fake customer payments or
autonomous bookings are executed by this component.
"""
from datetime import UTC, datetime, timedelta

import pytest
from flask import Flask

from mission_control import (
    barber_sika,
    barber_supply_extension,
    travel_marketplace,
    travel_supply_core,
    travel_supply_views,
)


def _quote(**overrides):
    start = datetime.now(UTC) + timedelta(days=2)
    payload = {
        "source": "oap_direct",
        "category": "barber",
        "listing_id": "11111111-1111-4111-8111-111111111111",
        "slot_id": "22222222-2222-4222-8222-222222222222",
        "supplier_id": "33333333-3333-4333-8333-333333333333",
        "supplier_name": "Certified Local Barber",
        "title": "Owner-listed haircut service",
        "starts_at": start.isoformat(),
        "ends_at": (start + timedelta(minutes=40)).isoformat(),
        "observed_at": datetime.now(UTC).isoformat(),
        "requested_quantity": 1,
        "unit_price_minor": 2500,
        "total_price_minor": 2500,
        "currency": "GBP",
        "provider_authority": False,
        "observed_not_inferred": True,
    }
    payload.update(overrides)
    return payload


def _ready(monkeypatch, value=True):
    monkeypatch.setattr(
        barber_sika.barber_supply_extension,
        "status",
        lambda: {"schema_ready": value},
    )


def test_supply_migration_is_additive_and_does_not_rewrite_core():
    assert barber_supply_extension.VERSION != travel_supply_core.SUPPLY_CORE_MIGRATION_VERSION
    assert "barber" in travel_supply_core.SUPPLY_CATEGORIES
    assert "service" in travel_supply_core.SUPPLIER_TYPES
    assert "barber" not in "\n".join(travel_supply_core.SUPPLY_CORE_SCHEMA_STATEMENTS)
    assert "barber" in "\n".join(barber_supply_extension.STATEMENTS)


def test_schema_needs_explicit_human_approval():
    with pytest.raises(RuntimeError, match="explicit_human_approval_required"):
        barber_supply_extension.init_schema()


def test_schema_fails_closed_when_base_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        barber_supply_extension.travel_supply_core,
        "supply_core_schema_status",
        lambda: {"schema_ready": False},
    )
    assert barber_supply_extension.status()["schema_ready"] is False
    with pytest.raises(RuntimeError, match="base_supply_schema_not_ready"):
        barber_supply_extension.init_schema(assume_yes=True)


def test_barber_sika_uses_certified_db_price_not_client_price(monkeypatch):
    _ready(monkeypatch)
    called = []

    def real_quote(payload):
        called.append(payload)
        return _quote()

    monkeypatch.setattr(travel_marketplace, "quote_direct", real_quote)
    result = barber_sika.quote_for_slot({
        "listing_id": "11111111-1111-4111-8111-111111111111",
        "starts_at": "2099-01-01T10:00:00+00:00",
        "ends_at": "2099-01-01T10:40:00+00:00",
        "amount_sika": 1,  # Client-supplied price is never trusted.
        "quantity": 1,
    })
    assert called[0]["quantity"] == 1
    assert "amount_sika" not in called[0]
    assert result["sika_amount"] == "25.00"
    assert result["gbp_amount"] == "25.00"
    assert result["booking_state"] == "QUOTE_ONLY"
    assert result["payment_authorised"] is False
    assert result["settlement_proven"] is False
    assert result["money_moved"] is False
    assert result["supplier_confirmed"] is False


@pytest.mark.parametrize("override", [
    {"category": "event"},
    {"source": "third_party"},
    {"observed_not_inferred": False},
    {"provider_authority": True},
    {"requested_quantity": 2},
    {"currency": "USD"},
    {"total_price_minor": 0, "unit_price_minor": 0},
    {"unit_price_minor": 3000},
    {"starts_at": "2020-01-01T10:00:00+00:00"},
])
def test_barber_quote_rejects_untrusted_or_invalid_slot(monkeypatch, override):
    _ready(monkeypatch)
    monkeypatch.setattr(travel_marketplace, "quote_direct", lambda _: _quote(**override))
    with pytest.raises(ValueError):
        barber_sika.quote_for_slot({
            "listing_id": "verified",
            "starts_at": "2099-01-01T10:00:00+00:00",
            "ends_at": "2099-01-01T10:40:00+00:00",
        })


def test_no_quote_when_barber_schema_unready(monkeypatch):
    _ready(monkeypatch, False)
    with pytest.raises(RuntimeError, match="barber_supply_schema_not_ready"):
        barber_sika.quote_for_slot({})


@pytest.mark.parametrize("bad", [True, 2, 0, "1", None])
def test_only_one_real_appointment_per_quote(monkeypatch, bad):
    _ready(monkeypatch)
    with pytest.raises(ValueError, match="one_appointment_per_booking_required"):
        barber_sika.quote_for_slot({"quantity": bad})


def test_offer_endpoint_fails_closed_until_schema_ready(monkeypatch):
    monkeypatch.setattr(
        travel_supply_views.barber_supply_extension,
        "status",
        lambda: {"schema_ready": False},
    )
    app = Flask(__name__)
    app.register_blueprint(travel_supply_views.bp)
    response = app.test_client().get("/local/barbers/api/offers")
    assert response.status_code == 503
    assert response.headers["Cache-Control"] == "no-store"


def test_offer_endpoint_reuses_only_certified_barber_supply(monkeypatch):
    monkeypatch.setattr(
        travel_supply_views.barber_supply_extension,
        "status",
        lambda: {"schema_ready": True},
    )
    seen = []

    def offers(**kwargs):
        seen.append(kwargs)
        return {"ready": True, "count": 0, "offers": [], "source": "oap_direct"}

    monkeypatch.setattr(travel_supply_views.travel_marketplace, "public_offers", offers)
    app = Flask(__name__)
    app.register_blueprint(travel_supply_views.bp)
    response = app.test_client().get("/local/barbers/api/offers")
    assert response.status_code == 200
    assert response.get_json()["offers"] == []
    assert seen[0]["category"] == "barber"
    assert response.headers["Cache-Control"] == "no-store"


def test_barber_http_quote_never_claims_customer_paid(monkeypatch):
    monkeypatch.setattr(
        travel_supply_views.barber_sika,
        "quote_for_slot",
        lambda _: {"booking_state": "QUOTE_ONLY", "money_moved": False},
    )
    app = Flask(__name__)
    app.register_blueprint(travel_supply_views.bp)
    response = app.test_client().post(
        "/local/barbers/api/sika-quote", json={"listing_id": "verified"}
    )
    assert response.status_code == 200
    assert response.get_json()["money_moved"] is False
    assert response.headers["Cache-Control"] == "no-store"
