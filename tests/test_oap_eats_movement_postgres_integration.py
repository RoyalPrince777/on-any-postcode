"""Ephemeral PostgreSQL proof of Eats permissions and atomic Movement binding.

The explicit CI gate and loopback-only database guard prevent these schema
fixtures from being pointed at a remote application database.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Barrier
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
from psycopg import sql

from mission_control import (
    movement_operations,
    oap_eats_fulfilment,
    oap_eats_store,
    postgres_db,
    sika_account_engine,
    sika_payment_orchestrator,
    sika_payment_reservations,
)

pytestmark = pytest.mark.skipif(
    os.getenv("OAP_REAL_POSTGRES_PROOF") != "1",
    reason="Real Eats/Movement PostgreSQL proof requires the explicit CI gate",
)


@pytest.fixture
def delivery(monkeypatch):
    url = postgres_db._database_url()
    assert urlsplit(url).hostname in {"127.0.0.1", "localhost", "::1"}, "Ephemeral loopback database required"
    original_connect = postgres_db.connect
    schema = "oap_eats_test_" + uuid4().hex
    with original_connect() as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        db.commit()

    @contextmanager
    def connect(*, readonly=False):
        with original_connect(readonly=readonly) as db:
            db.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            db.execute("SET LOCAL statement_timeout = '10s'")
            yield db

    monkeypatch.setattr(postgres_db, "connect", connect)
    try:
        with connect() as db:
            for statement in (
                *postgres_db.MIGRATION_STATEMENTS,
                *movement_operations.MOVEMENT_SCHEMA_STATEMENTS,
                *oap_eats_store.SCHEMA_STATEMENTS,
                *sika_account_engine.SCHEMA_STATEMENTS,
                *sika_payment_orchestrator.SCHEMA_STATEMENTS,
                *sika_payment_reservations.SCHEMA_STATEMENTS,
            ):
                db.execute(statement)
            customer, merchant, outsider, order = (str(uuid4()) for _ in range(4))
            for identity in (customer, merchant, outsider):
                db.execute("INSERT INTO users(id,username) VALUES (%s,%s)", (identity, identity))
            db.execute(
                "INSERT INTO oap_eats_merchants(merchant_id,owner_identity_id,name,active) VALUES (%s,%s,'CI merchant',TRUE)",
                (merchant, merchant),
            )
            db.execute(
                """INSERT INTO oap_eats_orders(order_id,customer_identity_id,merchant_id,
                       state,items,amount_minor,currency,fulfilment_mode,idempotency_key)
                   VALUES (%s,%s,%s,'authorised','[]',1599,'GBP','delivery',%s)""",
                (order, customer, merchant, "order-" + order),
            )
            db.commit()
        yield {
            "order_id": order, "customer_identity_id": customer,
            "merchant": merchant, "outsider": outsider,
            "pickup": {"label": "Mitcham", "zone": "CR4", "latitude": 51.4036, "longitude": -0.1687},
            "destination": {"label": "London Bridge", "zone": "SE1", "latitude": 51.5079, "longitude": -0.0877},
            "idempotency_key": "delivery-" + order,
        }
    finally:
        with original_connect() as db:
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
            db.commit()


def _create(delivery, **changes):
    args = {key: value for key, value in delivery.items() if key not in {"merchant", "outsider"}}
    return oap_eats_fulfilment.create_delivery(**{**args, **changes})


def _readback(delivery):
    # Fresh connection: assertions see only committed records.
    with postgres_db.connect(readonly=True) as db:
        bookings = db.execute("SELECT booking_id FROM oap_movement_bookings").fetchall()
        bound = db.execute(
            "SELECT movement_booking_id FROM oap_eats_orders WHERE order_id=%s",
            (delivery["order_id"],),
        ).fetchone()[0]
    return [str(row[0]) for row in bookings], str(bound) if bound else None


@pytest.mark.parametrize("caller", ["merchant", "outsider"])
def test_non_customer_cannot_create_any_movement_row(delivery, caller):
    with pytest.raises(PermissionError, match="order_customer_required"):
        _create(delivery, customer_identity_id=delivery[caller])
    assert _readback(delivery) == ([], None)


@pytest.mark.parametrize("after_binding", [False, True])
def test_failure_before_commit_rolls_back_booking_and_binding(delivery, monkeypatch, after_binding):
    original = oap_eats_store.STORE.bind_movement

    def fail(**kwargs):
        if after_binding:
            original(**kwargs)
        raise RuntimeError("injected_binding_failure")

    with monkeypatch.context() as patch:
        patch.setattr(oap_eats_store.STORE, "bind_movement", fail)
        with pytest.raises(RuntimeError, match="injected_binding_failure"):
            _create(delivery)
    assert _readback(delivery) == ([], None)
    result = _create(delivery)
    assert _readback(delivery) == ([result["movement_booking_id"]], result["movement_booking_id"])
    assert result["courier_dispatched"] is False
    assert result["external_dispatch_enabled"] is False


def test_lost_response_same_key_retry_reads_one_committed_booking(delivery):
    first = _create(delivery)
    replay = _create(delivery)
    assert first["movement_booking_id"] == replay["movement_booking_id"]
    assert _readback(delivery) == ([first["movement_booking_id"]], first["movement_booking_id"])


def test_changed_payload_same_key_is_rejected_without_extra_booking(delivery):
    first = _create(delivery)
    with pytest.raises(ValueError, match="idempotency_conflict"):
        _create(delivery, destination={"label": "Brixton", "zone": "SW9", "latitude": 51.462, "longitude": -0.115})
    assert _readback(delivery) == ([first["movement_booking_id"]], first["movement_booking_id"])


def test_changed_key_cannot_leave_an_orphan_after_existing_binding(delivery):
    first = _create(delivery)
    with pytest.raises(PermissionError, match="order_movement_binding_denied"):
        _create(delivery, idempotency_key=delivery["idempotency_key"] + "-other")
    assert _readback(delivery) == ([first["movement_booking_id"]], first["movement_booking_id"])


@pytest.mark.parametrize("same_key", [True, False])
def test_concurrent_requests_commit_only_one_order_booking(delivery, same_key):
    barrier = Barrier(2)

    def worker(index):
        barrier.wait(timeout=10)
        key = delivery["idempotency_key"] + ("" if same_key else f"-{index}")
        try:
            return _create(delivery, idempotency_key=key)["movement_booking_id"]
        except PermissionError as exc:
            assert str(exc) == "order_movement_binding_denied"
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, (0, 1)))
    bookings, bound = _readback(delivery)
    assert bookings == [bound]
    assert results.count(bound) == (2 if same_key else 1)
    assert results.count(None) == (0 if same_key else 1)


@pytest.mark.parametrize("state,mode,error", [
    ("created", "delivery", "order_not_ready_for_delivery_booking"),
    ("authorised", "collection", "delivery_not_required"),
])
def test_ineligible_order_cannot_create_booking(delivery, state, mode, error):
    with postgres_db.connect() as db:
        db.execute("UPDATE oap_eats_orders SET state=%s,fulfilment_mode=%s WHERE order_id=%s", (state, mode, delivery["order_id"]))
        db.commit()
    with pytest.raises(ValueError, match=error):
        _create(delivery)
    assert _readback(delivery) == ([], None)


# Independent acceptance cases for the generic customer/merchant endpoint.
# Database fixtures below label software states; they attest no physical event.
_PUBLIC_STATE_CASES = [
    ("created", "authorised", ()),
    ("created", "cancelled", ("customer", "merchant")),
    ("created", "failed", ()),
    ("authorised", "confirmed", ("merchant",)),
    ("authorised", "refunded", ()),
    ("authorised", "failed", ()),
    ("confirmed", "preparing", ("merchant",)),
    ("confirmed", "cancelled", ("customer", "merchant")),
    ("preparing", "ready", ("merchant",)),
    ("preparing", "cancelled", ("customer", "merchant")),
    ("ready", "courier_assigned", ()),
    ("ready", "collected", ()),
    ("ready", "cancelled", ("customer", "merchant")),
    ("courier_assigned", "collected", ()),
    ("courier_assigned", "cancelled", ("customer", "merchant")),
    ("collected", "delivered", ()),
    ("collected", "disputed", ("customer",)),
    ("delivered", "settlement_pending", ()),
    ("delivered", "disputed", ("customer",)),
    ("settlement_pending", "settled", ()),
    ("settlement_pending", "disputed", ("customer",)),
    ("settled", "disputed", ("customer",)),
    ("cancelled", "refunded", ()),
    ("disputed", "refunded", ()),
    ("disputed", "settled", ()),
]


def _order_readback(delivery):
    with postgres_db.connect(readonly=True) as db:
        state, payment, hold = db.execute(
            "SELECT state,payment_id,payment_hold_id FROM oap_eats_orders WHERE order_id=%s",
            (delivery["order_id"],),
        ).fetchone()
        events = db.execute(
            "SELECT count(*) FROM oap_eats_order_events WHERE order_id=%s",
            (delivery["order_id"],),
        ).fetchone()[0]
    return state, payment, hold, events


@pytest.mark.parametrize("source,target,allowed_roles", _PUBLIC_STATE_CASES)
@pytest.mark.parametrize("role", ["customer", "merchant", "outsider"])
def test_public_state_authority_is_owner_role_specific(delivery, source, target, allowed_roles, role):
    with postgres_db.connect() as db:
        db.execute("UPDATE oap_eats_orders SET state=%s WHERE order_id=%s", (source, delivery["order_id"]))
        db.commit()
    identity = delivery["customer_identity_id"] if role == "customer" else delivery[role]
    args = {"order_id": delivery["order_id"], "actor_identity_id": identity, "target_state": target}
    if role in allowed_roles:
        result = oap_eats_store.STORE.transition(**args)
        assert result["state"] == target
        assert result["payment_captured"] is False
        assert result["courier_dispatched"] is False
        assert _order_readback(delivery) == (target, None, None, 1)
    else:
        with pytest.raises(PermissionError, match="order_not_owned|order_transition_role_denied"):
            oap_eats_store.STORE.transition(**args)
        assert _order_readback(delivery) == (source, None, None, 0)
    assert _readback(delivery) == ([], None)


def test_invalid_state_skip_is_rejected_without_event(delivery):
    with pytest.raises(ValueError, match="order_transition_not_allowed"):
        oap_eats_store.STORE.transition(
            order_id=delivery["order_id"], actor_identity_id=delivery["merchant"], target_state="settled",
        )
    assert _order_readback(delivery) == ("authorised", None, None, 0)


@pytest.fixture
def payment(delivery):
    account, intent, hold = (str(uuid4()) for _ in range(3))
    with postgres_db.connect() as db:
        db.execute(
            """INSERT INTO oap_sika_accounts(account_id,owner_reference,legal_entity,
                   jurisdiction,currency,ledger_account_id,status)
               VALUES (%s,%s,'CI fixture','United Kingdom','GBP',%s,'OPEN')""",
            (account, delivery["customer_identity_id"], "ledger-" + account),
        )
        db.execute(
            """INSERT INTO oap_sika_payment_intents(payment_id,idempotency_key,payer_account_id,
                   payee_reference,amount,currency,jurisdiction,status)
               VALUES (%s,%s,%s,%s,15.99,'GBP','United Kingdom','AUTHORISED')""",
            (intent, "intent-" + intent, account, delivery["merchant"]),
        )
        db.execute(
            """INSERT INTO oap_sika_payment_holds(hold_id,payment_id,payer_account_id,amount,currency,status)
               VALUES (%s,%s,%s,15.99,'GBP','ACTIVE')""", (hold, intent, account),
        )
        db.commit()
    return {"account": account, "intent": intent, "hold": hold}


def _bind_payment(delivery, payment, **changes):
    return oap_eats_fulfilment.bind_payment(**{
        "order_id": delivery["order_id"], "customer_identity_id": delivery["customer_identity_id"],
        "payment_id": payment["intent"], **changes,
    })


def test_owned_payment_binding_persists_without_executing_payment(delivery, payment):
    result = _bind_payment(delivery, payment)
    assert _order_readback(delivery) == ("authorised", payment["intent"], payment["hold"], 1)
    assert result["payment_status"] == "AUTHORISED"
    assert result["hold_status"] == "ACTIVE"
    assert result["payment_captured"] is False
    assert result["money_moved_by_eats"] is False
    with postgres_db.connect(readonly=True) as db:
        assert db.execute("SELECT status FROM oap_sika_payment_intents WHERE payment_id=%s", (payment["intent"],)).fetchone()[0] == "AUTHORISED"
        assert db.execute("SELECT status FROM oap_sika_payment_holds WHERE hold_id=%s", (payment["hold"],)).fetchone()[0] == "ACTIVE"


@pytest.mark.parametrize("caller", ["merchant", "outsider"])
def test_non_customer_cannot_bind_payment(delivery, payment, caller):
    with pytest.raises(PermissionError, match="order_customer_required"):
        _bind_payment(delivery, payment, customer_identity_id=delivery[caller])
    assert _order_readback(delivery) == ("authorised", None, None, 0)


@pytest.mark.parametrize("change", ["foreign_owner", "FROZEN", "CLOSED", "missing", "currency"])
def test_payer_account_must_be_owned_open_and_matching_currency(delivery, payment, change):
    with postgres_db.connect() as db:
        if change == "foreign_owner":
            db.execute("UPDATE oap_sika_accounts SET owner_reference=%s WHERE account_id=%s", (delivery["outsider"], payment["account"]))
        elif change == "missing":
            db.execute("DELETE FROM oap_sika_accounts WHERE account_id=%s", (payment["account"],))
        elif change == "currency":
            db.execute("UPDATE oap_sika_accounts SET currency='USD' WHERE account_id=%s", (payment["account"],))
        else:
            db.execute("UPDATE oap_sika_accounts SET status=%s WHERE account_id=%s", (change, payment["account"]))
        db.commit()
    error = ValueError if change == "currency" else PermissionError
    with pytest.raises(error, match="payment_currency_mismatch|payment_payer_not_owned_or_open"):
        _bind_payment(delivery, payment)
    assert _order_readback(delivery) == ("authorised", None, None, 0)


@pytest.mark.parametrize("state", ["DRAFT", "REVIEW", "SETTLED", "FAILED", "CANCELLED"])
def test_intent_label_cannot_bypass_payment_binding_eligibility(delivery, payment, state):
    with postgres_db.connect() as db:
        db.execute("UPDATE oap_sika_payment_intents SET status=%s WHERE payment_id=%s", (state, payment["intent"]))
        db.commit()
    with pytest.raises(ValueError, match="payment_intent_not_bindable"):
        _bind_payment(delivery, payment)
    assert _order_readback(delivery) == ("authorised", None, None, 0)


@pytest.mark.parametrize("change", ["payer", "amount", "currency", "inactive", "missing"])
def test_inconsistent_hold_never_binds(delivery, payment, change):
    statements = {
        "payer": "UPDATE oap_sika_payment_holds SET payer_account_id='other' WHERE hold_id=%s",
        "amount": "UPDATE oap_sika_payment_holds SET amount=1 WHERE hold_id=%s",
        "currency": "UPDATE oap_sika_payment_holds SET currency='USD' WHERE hold_id=%s",
        "inactive": "UPDATE oap_sika_payment_holds SET status='RELEASED' WHERE hold_id=%s",
        "missing": "DELETE FROM oap_sika_payment_holds WHERE hold_id=%s",
    }
    with postgres_db.connect() as db:
        db.execute(statements[change], (payment["hold"],))
        db.commit()
    with pytest.raises(ValueError):
        _bind_payment(delivery, payment)
    assert _order_readback(delivery) == ("authorised", None, None, 0)


@pytest.mark.parametrize("change", ["foreign_owner", "closed"])
def test_payment_write_rechecks_account_after_preflight(delivery, payment, monkeypatch, change):
    original = oap_eats_store.STORE.bind_payment
    def change_account_then_bind(**kwargs):
        with postgres_db.connect() as db:
            if change == "foreign_owner":
                db.execute("UPDATE oap_sika_accounts SET owner_reference=%s WHERE account_id=%s", (delivery["outsider"], payment["account"]))
            else:
                db.execute("UPDATE oap_sika_accounts SET status='CLOSED' WHERE account_id=%s", (payment["account"],))
            db.commit()
        return original(**kwargs)
    monkeypatch.setattr(oap_eats_store.STORE, "bind_payment", change_account_then_bind)
    with pytest.raises(PermissionError, match="order_payment_binding_denied"):
        _bind_payment(delivery, payment)
    assert _order_readback(delivery) == ("authorised", None, None, 0)
