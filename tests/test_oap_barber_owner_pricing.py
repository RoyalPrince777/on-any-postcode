"""Owner-only barber price UI, amount validation and committed-price protection."""
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from flask import Flask

from mission_control import (
    barber_owner_pricing,
    barber_owner_views,
    travel_supply_core,
    web_security,
)


OWNER = "11111111-1111-4111-8111-111111111111"
SLOT = "22222222-2222-4222-8222-222222222222"


class _Result:
    def __init__(self, *, one=None, many=()):
        self.one = one
        self.many = many

    def fetchone(self):
        return self.one

    def fetchall(self):
        return list(self.many)


class _Connection:
    def __init__(self, *, one=None, many=()):
        self.one = one
        self.many = many
        self.query = ""
        self.params = ()
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, sql, params=()):
        self.query = sql
        self.params = params
        return _Result(one=self.one, many=self.many)

    def commit(self):
        self.committed = True


def _db(monkeypatch, connection):
    monkeypatch.setattr(
        barber_owner_pricing.barber_supply_extension,
        "status",
        lambda: {"schema_ready": True},
    )
    monkeypatch.setattr(
        barber_owner_pricing.postgres_db,
        "connect",
        lambda readonly=False: connection,
    )


@pytest.mark.parametrize("bad", [
    None, "", "abc", "NaN", "Infinity", "-2", "0", "0.00",
    "1.001", "10000.01", True,
])
def test_bad_owner_price_is_rejected(bad):
    with pytest.raises(ValueError):
        barber_owner_pricing._price_minor(bad)


def test_valid_sika_amount_uses_pennies_without_float_rounding():
    assert barber_owner_pricing._price_minor("15.75") == 1575
    assert barber_owner_pricing._price_minor(Decimal("25.00")) == 2500


def test_price_update_requires_certified_owned_future_unheld_slot(monkeypatch):
    observed = datetime.now(UTC)
    conn = _Connection(one=(SLOT, 1575, observed))
    _db(monkeypatch, conn)
    result = barber_owner_pricing.update_price(
        owner_identity_id=OWNER,
        slot_id=SLOT,
        amount_sika="15.75",
    )
    sql = conn.query
    assert "p.owner_identity_id=%s" in sql
    assert "p.supplier_type='service'" in sql
    assert "l.category='barber'" in sql
    assert "p.state='CERTIFIED'" in sql
    assert "s.starts_at>CURRENT_TIMESTAMP" in sql
    assert "s.capacity_held=0 AND s.capacity_confirmed=0" in sql
    assert conn.params == (1575, SLOT, OWNER)
    assert conn.committed is True
    assert result["amount_sika"] == "15.75"
    assert result["money_moved"] is False
    assert result["payment_authorised"] is False


def test_price_update_fails_closed_when_slot_is_booked_or_other_owner(monkeypatch):
    conn = _Connection(one=None)
    _db(monkeypatch, conn)
    with pytest.raises(PermissionError, match="slot_not_owned_or_price_locked"):
        barber_owner_pricing.update_price(
            owner_identity_id=OWNER, slot_id=SLOT, amount_sika="30"
        )
    assert conn.committed is False


def test_owner_can_only_read_own_approved_barber_slots(monkeypatch):
    now = datetime.now(UTC)
    conn = _Connection(many=[(
        SLOT, "33333333-3333-4333-8333-333333333333",
        "Haircut", "Own Barber", now + timedelta(days=1),
        now + timedelta(days=1, minutes=30), 2500, "GBP", 0, 0,
        "ACTIVE", now,
    )])
    _db(monkeypatch, conn)
    result = barber_owner_pricing.owner_slots(owner_identity_id=OWNER)
    assert conn.params == (OWNER,)
    assert "p.owner_identity_id=%s" in conn.query
    assert "l.category='barber'" in conn.query
    assert result["count"] == 1
    assert result["slots"][0]["amount_sika"] == "25.00"
    assert result["slots"][0]["editable"] is True
    assert "buyer_identity_id" not in result["slots"][0]
    assert result["payment_enabled"] is False


def _app(monkeypatch, *, logged_in=True):
    monkeypatch.setattr(
        web_security,
        "current_authenticated_user",
        lambda: {"id": OWNER} if logged_in else None,
    )
    app = Flask(__name__, template_folder="../mission_control/templates")
    app.secret_key = "test-only-local-cookie"
    app.register_blueprint(barber_owner_views.bp)
    return app


def test_owner_price_api_requires_authentication(monkeypatch):
    app = _app(monkeypatch, logged_in=False)
    response = app.test_client().get("/local/barbers/manage/api")
    assert response.status_code == 401


def test_owner_price_update_requires_csrf(monkeypatch):
    app = _app(monkeypatch)
    response = app.test_client().post(
        "/local/barbers/manage/api/prices",
        json={"slot_id": SLOT, "amount_sika": "30.00"},
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"


def test_owner_identity_is_server_side_not_client_controlled(monkeypatch):
    observed = {}

    def edit(**kwargs):
        observed.update(kwargs)
        return {"amount_sika": kwargs["amount_sika"], "money_moved": False}

    monkeypatch.setattr(barber_owner_views.barber_owner_pricing, "update_price", edit)
    app = _app(monkeypatch)
    client = app.test_client()
    with client.session_transaction() as s:
        s[web_security.CSRF_SESSION_KEY] = "s" * 48
    response = client.post(
        "/local/barbers/manage/api/prices",
        json={
            "slot_id": SLOT,
            "amount_sika": "20.00",
            "owner_identity_id": "99999999-9999-4999-8999-999999999999",
        },
        headers={"X-OAP-CSRF": "s" * 48},
    )
    assert response.status_code == 200
    assert observed["owner_identity_id"] == OWNER
    assert response.get_json()["money_moved"] is False
    assert response.headers["Cache-Control"] == "no-store"


def test_owner_dashboard_has_usable_price_editor(monkeypatch):
    monkeypatch.setattr(
        barber_owner_views.barber_owner_pricing,
        "owner_slots",
        lambda **_: {"slots": [{
            "slot_id": SLOT, "service": "Owner haircut",
            "business": "Owner Barber", "starts_at": "2026-11-01T09:00:00+00:00",
            "ends_at": "2026-11-01T09:30:00+00:00",
            "amount_sika": "20.00", "editable": True,
        }]},
    )
    app = _app(monkeypatch)
    res = app.test_client().get("/local/barbers/manage")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "My Services &amp; Prices" in html
    assert "Save my price" in html
    assert "20.00" in html
    assert "No payment taken" in html
    assert res.headers["Cache-Control"] == "no-store"


def test_core_upsert_does_not_reprice_held_or_booked_inventory():
    original = "\n".join(travel_supply_core.SUPPLY_CORE_SCHEMA_STATEMENTS)
    # The schema's migration checksum must remain stable; new invariant is in
    # the runtime UPDATE/UPSERT, not in original v0007 schema statements.
    assert "price_minor=EXCLUDED.price_minor" not in original
    import inspect

    source = inspect.getsource(
        travel_supply_core.PostgresTravelSupplyStore.set_inventory_slot
    )
    assert "capacity_held=0" in source
    assert "capacity_confirmed=0" in source
    assert "price_minor=EXCLUDED.price_minor" in source
