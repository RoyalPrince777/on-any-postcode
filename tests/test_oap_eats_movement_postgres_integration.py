"""Ephemeral PostgreSQL proof of Eats permissions and atomic Movement binding.

The explicit CI gate and loopback-only database guard prevent these schema
fixtures from being pointed at a remote application database.
"""
from __future__ import annotations

import json
import os
import select
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier, Event
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
from psycopg import errors, sql

from mission_control import (
    global_journey_schema,
    global_journey_store,
    movement_match_safety,
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
                *global_journey_schema.STATEMENTS,
                *global_journey_schema.LIFECYCLE_STATEMENTS,
                *oap_eats_store.SCHEMA_STATEMENTS,
                *oap_eats_store.INTEGRITY_SCHEMA_STATEMENTS,
                *sika_account_engine.SCHEMA_STATEMENTS,
                *sika_payment_orchestrator.SCHEMA_STATEMENTS,
                *sika_payment_reservations.SCHEMA_STATEMENTS,
            ):
                db.execute(statement)
            customer, merchant, outsider, order = (str(uuid4()) for _ in range(4))
            for identity in (customer, merchant, outsider):
                db.execute("INSERT INTO users(id,username) VALUES (%s,%s)", (identity, identity))
                db.execute("INSERT INTO oap_identities(identity_id,display_name,identity_type,status) VALUES (%s,%s,'PERSON','ACTIVE')", (identity, identity))
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
            # Existing lifecycle/payment cases seed their accepted order state.
            # Catalogue creation itself is exercised separately below.
            db.execute("UPDATE oap_eats_orders SET pricing_version=%s WHERE order_id=%s", (oap_eats_store.PRICING_VERSION, order))
            db.commit()
        monkeypatch.setenv("OAP_EATS_TEST_SCHEMA", schema)
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


def _seed_payment(delivery):
    account, intent, hold, payee = (str(uuid4()) for _ in range(4))
    with postgres_db.connect() as db:
        db.execute(
            """INSERT INTO oap_sika_accounts(account_id,owner_reference,legal_entity,
                   jurisdiction,currency,ledger_account_id,status)
               VALUES (%s,%s,'CI merchant','United Kingdom','GBP',%s,'OPEN')""",
            (payee, delivery["merchant"], "ledger-" + payee),
        )
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
            (intent, "intent-" + intent, account, payee),
        )
        db.execute(
            """INSERT INTO oap_sika_payment_holds(hold_id,payment_id,payer_account_id,amount,currency,status)
               VALUES (%s,%s,%s,15.99,'GBP','ACTIVE')""", (hold, intent, account),
        )
        db.commit()
    return {"account": account, "intent": intent, "hold": hold, "payee": payee, "merchant": delivery["merchant"]}


@pytest.fixture
def payment(delivery):
    return _seed_payment(delivery)


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


@pytest.fixture
def catalogue(delivery):
    first, second = sorted(str(uuid4()) for _ in range(2))
    with postgres_db.connect() as db:
        for item, name, amount in [(first, "Meal", 1200), (second, "Side", 399)]:
            db.execute(
                """INSERT INTO oap_eats_menu_items(item_id,merchant_id,name,amount_minor,currency)
                   VALUES (%s,%s,%s,%s,'GBP')""", (item, delivery["merchant"], name, amount),
            )
        db.commit()
    return [{"item_id": item, "quantity": 1} for item in (first, second)]


def _catalogue_order(delivery, catalogue, **changes):
    return oap_eats_store.STORE.create_order(**{
        "customer_identity_id": delivery["customer_identity_id"], "merchant_id": delivery["merchant"],
        "items": catalogue, "amount_minor": None, "currency": "GBP", "fulfilment_mode": "delivery",
        "idempotency_key": "catalogue-" + delivery["order_id"], **changes,
    })


def test_catalogue_price_snapshot_and_payment_binding(delivery, catalogue, payment):
    result = _catalogue_order(delivery, catalogue)
    assert result["amount_minor"] == 1599
    assert result["state"] == "created"
    assert result["payment_captured"] is result["courier_dispatched"] is False
    with postgres_db.connect(readonly=True) as db:
        items, version = db.execute("SELECT items,pricing_version FROM oap_eats_orders WHERE order_id=%s", (result["order_id"],)).fetchone()
    assert version == oap_eats_store.PRICING_VERSION
    assert [item["unit_amount_minor"] for item in items] == [1200, 399]
    assert [item["name"] for item in items] == ["Meal", "Side"]
    bound = _bind_payment({**delivery, "order_id": result["order_id"]}, payment)
    assert bound["payment_id"] == payment["intent"]
    assert bound["money_moved_by_eats"] is False
    with postgres_db.connect(readonly=True) as db:
        evidence = db.execute(
            "SELECT evidence FROM oap_eats_order_events WHERE order_id=%s AND evidence ? 'payment_id'",
            (result["order_id"],),
        ).fetchone()[0]
    assert evidence["payee_account_id"] == payment["payee"]
    assert evidence["merchant_id"] == delivery["merchant"]


def test_retry_retains_original_quote_after_catalogue_change(delivery, catalogue):
    first = _catalogue_order(delivery, catalogue, amount_minor=1599)
    with postgres_db.connect() as db:
        db.execute("UPDATE oap_eats_menu_items SET amount_minor=9999,available=FALSE WHERE merchant_id=%s", (delivery["merchant"],))
        db.execute("UPDATE oap_eats_merchants SET active=FALSE WHERE merchant_id=%s", (delivery["merchant"],))
        db.commit()
    replay = _catalogue_order(delivery, list(reversed(catalogue)), amount_minor=1599)
    assert replay == first
    assert _order_readback({**delivery, "order_id": first["order_id"]}) == ("created", None, None, 1)


@pytest.mark.parametrize("change", ["underquote", "overquote", "boolean_total", "float_total", "text_total",
                                  "price_override", "quantity_zero", "quantity_bool", "quantity_float",
                                  "quantity_text", "quantity_excess", "duplicate", "invalid_item", "missing_quantity"])
def test_client_cannot_create_an_unpriced_or_ambiguous_order(delivery, catalogue, change):
    changes = {}
    items = [dict(item) for item in catalogue]
    totals = {"underquote": 1, "overquote": 1600, "boolean_total": True, "float_total": 1599.0, "text_total": "1599"}
    quantities = {"quantity_zero": 0, "quantity_bool": True, "quantity_float": 1.0, "quantity_text": "1", "quantity_excess": 100}
    if change in totals:
        changes["amount_minor"] = totals[change]
    elif change in quantities:
        items[0]["quantity"] = quantities[change]
    elif change == "price_override":
        items[0]["unit_amount_minor"] = 1
    elif change == "duplicate":
        items.append(dict(items[0]))
    elif change == "invalid_item":
        items[0]["item_id"] = "meal-1"
    else:
        del items[0]["quantity"]
    with pytest.raises(ValueError):
        _catalogue_order(delivery, items, **changes)
    with postgres_db.connect(readonly=True) as db:
        assert db.execute("SELECT count(*) FROM oap_eats_orders").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM oap_eats_order_events").fetchone()[0] == 0


@pytest.mark.parametrize("change,error", [("foreign", "menu_item_unavailable"), ("missing", "menu_item_unavailable"),
                                        ("unavailable", "menu_item_unavailable"), ("currency", "menu_currency_mismatch"),
                                        ("inactive_merchant", "merchant_unavailable"), ("overflow", "order_total_out_of_range")])
def test_catalogue_boundaries_fail_without_an_order(delivery, catalogue, change, error):
    with postgres_db.connect() as db:
        if change == "foreign":
            foreign = str(uuid4())
            db.execute("INSERT INTO oap_eats_merchants(merchant_id,owner_identity_id,name,active) VALUES (%s,%s,'Other',TRUE)", (foreign, delivery["outsider"]))
            db.execute("UPDATE oap_eats_menu_items SET merchant_id=%s WHERE item_id=%s", (foreign, catalogue[0]["item_id"]))
        elif change == "missing":
            db.execute("DELETE FROM oap_eats_menu_items WHERE item_id=%s", (catalogue[0]["item_id"],))
        elif change == "inactive_merchant":
            db.execute("UPDATE oap_eats_merchants SET active=FALSE WHERE merchant_id=%s", (delivery["merchant"],))
        else:
            assignments = {"unavailable": "available=FALSE", "currency": "currency='USD'", "overflow": "amount_minor=2147483647"}
            db.execute(sql.SQL("UPDATE oap_eats_menu_items SET " + assignments[change] + " WHERE item_id=%s"), (catalogue[0]["item_id"],))
        db.commit()
    with pytest.raises(ValueError, match=error):
        _catalogue_order(delivery, catalogue)
    with postgres_db.connect(readonly=True) as db:
        assert db.execute("SELECT count(*) FROM oap_eats_orders").fetchone()[0] == 1


@pytest.mark.parametrize("field", ["items", "merchant_id", "currency", "fulfilment_mode", "amount_minor"])
def test_existing_key_cannot_change_order_contract(delivery, catalogue, field):
    original = _catalogue_order(delivery, catalogue)
    changes = {"items": [catalogue[0]], "merchant_id": delivery["outsider"], "currency": "USD",
               "fulfilment_mode": "collection", "amount_minor": 1}
    with pytest.raises(ValueError, match="idempotency_conflict"):
        _catalogue_order(delivery, catalogue, **{field: changes[field]})
    assert _order_readback({**delivery, "order_id": original["order_id"]}) == ("created", None, None, 1)


@pytest.mark.parametrize("same_basket", [True, False])
def test_concurrent_order_creation_has_one_snapshot_and_event(delivery, catalogue, same_basket):
    barrier = Barrier(2)

    def worker(index):
        items = [dict(item) for item in catalogue]
        if index and not same_basket:
            items[0]["quantity"] = 2
        barrier.wait(timeout=10)
        try:
            return _catalogue_order(delivery, items)["order_id"]
        except ValueError as exc:
            assert str(exc) == "idempotency_conflict"
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, (0, 1)))
    assert len({result for result in results if result}) == 1
    assert results.count(None) == (0 if same_basket else 1)
    with postgres_db.connect(readonly=True) as db:
        assert db.execute("SELECT count(*) FROM oap_eats_orders").fetchone()[0] == 2
        assert db.execute("SELECT count(*) FROM oap_eats_order_events").fetchone()[0] == 1


@pytest.mark.parametrize("change", ["foreign_owner", "FROZEN", "CLOSED", "missing", "currency", "merchant_label", "customer_account"])
def test_payee_must_be_a_canonical_open_merchant_owned_account(delivery, payment, change):
    with postgres_db.connect() as db:
        if change == "foreign_owner":
            db.execute("UPDATE oap_sika_accounts SET owner_reference=%s WHERE account_id=%s", (delivery["outsider"], payment["payee"]))
        elif change == "missing":
            db.execute("DELETE FROM oap_sika_accounts WHERE account_id=%s", (payment["payee"],))
        elif change == "currency":
            db.execute("UPDATE oap_sika_accounts SET currency='USD' WHERE account_id=%s", (payment["payee"],))
        elif change in {"merchant_label", "customer_account"}:
            reference = delivery["merchant"] if change == "merchant_label" else payment["account"]
            db.execute("UPDATE oap_sika_payment_intents SET payee_reference=%s WHERE payment_id=%s", (reference, payment["intent"]))
        else:
            db.execute("UPDATE oap_sika_accounts SET status=%s WHERE account_id=%s", (change, payment["payee"]))
        db.commit()
    error = ValueError if change == "currency" else PermissionError
    with pytest.raises(error, match="payment_currency_mismatch|payment_payee_not_owned_by_merchant_or_open"):
        _bind_payment(delivery, payment)
    assert _order_readback(delivery) == ("authorised", None, None, 0)


@pytest.mark.parametrize("change", ["merchant_owner", "payee_owner", "payee_closed", "payee_reference", "unpriced_order"])
def test_payment_revalidates_merchant_and_pricing_after_preflight(delivery, payment, monkeypatch, change):
    original = oap_eats_store.STORE.bind_payment

    def change_then_bind(**kwargs):
        with postgres_db.connect() as db:
            if change == "merchant_owner":
                db.execute("UPDATE oap_eats_merchants SET owner_identity_id=%s WHERE merchant_id=%s", (delivery["outsider"], delivery["merchant"]))
            elif change == "payee_owner":
                db.execute("UPDATE oap_sika_accounts SET owner_reference=%s WHERE account_id=%s", (delivery["outsider"], payment["payee"]))
            elif change == "payee_closed":
                db.execute("UPDATE oap_sika_accounts SET status='CLOSED' WHERE account_id=%s", (payment["payee"],))
            elif change == "payee_reference":
                db.execute("UPDATE oap_sika_payment_intents SET payee_reference='arbitrary-merchant' WHERE payment_id=%s", (payment["intent"],))
            else:
                db.execute("UPDATE oap_eats_orders SET pricing_version=NULL WHERE order_id=%s", (delivery["order_id"],))
            db.commit()
        return original(**kwargs)

    monkeypatch.setattr(oap_eats_store.STORE, "bind_payment", change_then_bind)
    with pytest.raises((PermissionError, ValueError)):
        _bind_payment(delivery, payment)
    assert _order_readback(delivery) == ("authorised", None, None, 0)


def test_changed_payee_after_lock_hint_is_rejected(delivery, payment, monkeypatch):
    other = _seed_payment(delivery)
    connect = postgres_db.connect

    class ChangedPayeeConnection:
        def __init__(self, db):
            self.db = db

        def execute(self, statement, *args):
            if "SELECT account_id,owner_reference,status,currency" in str(statement):
                with connect() as writer:
                    writer.execute("UPDATE oap_sika_payment_intents SET payee_reference=%s WHERE payment_id=%s", (other["payee"], payment["intent"]))
                    writer.commit()
            return self.db.execute(statement, *args)

        def commit(self):
            self.db.commit()

    @contextmanager
    def changing_connect(*, readonly=False):
        with connect(readonly=readonly) as db:
            yield db if readonly else ChangedPayeeConnection(db)

    monkeypatch.setattr(postgres_db, "connect", changing_connect)
    with pytest.raises(ValueError, match="payment_payee_binding_changed"):
        _bind_payment(delivery, payment)
    assert _order_readback(delivery) == ("authorised", None, None, 0)


@pytest.mark.parametrize("version", [None, "unverified"])
def test_legacy_pricing_cannot_bind_or_replay_as_server_priced(delivery, catalogue, payment, version):
    with postgres_db.connect() as db:
        db.execute("UPDATE oap_eats_orders SET pricing_version=%s WHERE order_id=%s", (version, delivery["order_id"]))
        db.commit()
    with pytest.raises(ValueError, match="legacy_order_reprice_required"):
        _bind_payment(delivery, payment)
    with pytest.raises(ValueError, match="legacy_order_reprice_required"):
        _catalogue_order(delivery, catalogue, idempotency_key="order-" + delivery["order_id"])
    assert _order_readback(delivery) == ("authorised", None, None, 0)


def test_integrity_migration_is_recorded_and_leaves_legacy_orders_unverified(delivery, payment):
    with postgres_db.connect() as db:
        db.execute("ALTER TABLE oap_eats_orders DROP COLUMN pricing_version")
        db.commit()
    for _ in range(2):
        result = oap_eats_store.init_schema(assume_yes=True)
        assert result["integrity_checksum"] == oap_eats_store.INTEGRITY_MIGRATION_CHECKSUM
    with postgres_db.connect(readonly=True) as db:
        assert db.execute("SELECT pricing_version FROM oap_eats_orders WHERE order_id=%s", (delivery["order_id"],)).fetchone()[0] is None
        assert db.execute("SELECT checksum FROM oap_schema_migrations WHERE version=%s", (oap_eats_store.INTEGRITY_MIGRATION_VERSION,)).fetchall() == [(oap_eats_store.INTEGRITY_MIGRATION_CHECKSUM,)]
    with pytest.raises(ValueError, match="legacy_order_reprice_required"):
        _bind_payment(delivery, payment)


def test_integrity_migration_checksum_mismatch_fails_closed(delivery):
    with postgres_db.connect() as db:
        db.execute("INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,'different')", (oap_eats_store.INTEGRITY_MIGRATION_VERSION,))
        db.commit()
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        oap_eats_store.init_schema(assume_yes=True)


def test_catalogue_event_failure_rolls_back_order_and_allows_retry(delivery, catalogue):
    with postgres_db.connect() as db:
        db.execute("""CREATE FUNCTION reject_order_event() RETURNS trigger LANGUAGE plpgsql AS $$
                     BEGIN RAISE EXCEPTION 'injected_catalogue_event_failure'; END $$""")
        db.execute("CREATE TRIGGER reject_order_event BEFORE INSERT ON oap_eats_order_events FOR EACH ROW EXECUTE FUNCTION reject_order_event()")
        db.commit()
    with pytest.raises(errors.RaiseException, match="injected_catalogue_event_failure"):
        _catalogue_order(delivery, catalogue)
    with postgres_db.connect() as db:
        assert db.execute("SELECT count(*) FROM oap_eats_orders").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM oap_eats_order_events").fetchone()[0] == 0
        db.execute("DROP TRIGGER reject_order_event ON oap_eats_order_events")
        db.commit()
    result = _catalogue_order(delivery, catalogue)
    assert _order_readback({**delivery, "order_id": result["order_id"]}) == ("created", None, None, 1)


@pytest.mark.parametrize("merchant_change", [False, True])
def test_catalogue_snapshot_locks_prices_and_merchant_until_commit(delivery, catalogue, monkeypatch, merchant_change):
    connect = postgres_db.connect
    locked, release = Event(), Event()

    class PausedCatalogueConnection:
        def __init__(self, db):
            self.db = db

        def execute(self, statement, *args):
            if "INSERT INTO oap_eats_orders" in str(statement):
                locked.set()
                assert release.wait(timeout=10)
            return self.db.execute(statement, *args)

        def commit(self):
            self.db.commit()

    @contextmanager
    def paused_connect(*, readonly=False):
        with connect(readonly=readonly) as db:
            yield db if readonly else PausedCatalogueConnection(db)

    monkeypatch.setattr(postgres_db, "connect", paused_connect)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_catalogue_order, delivery, catalogue)
        try:
            assert locked.wait(timeout=10)
            with pytest.raises(errors.LockNotAvailable), connect() as db:
                db.execute("SET LOCAL lock_timeout = '250ms'")
                if merchant_change:
                    db.execute("UPDATE oap_eats_merchants SET active=FALSE WHERE merchant_id=%s", (delivery["merchant"],))
                else:
                    db.execute("UPDATE oap_eats_menu_items SET amount_minor=1 WHERE item_id=%s", (catalogue[0]["item_id"],))
                db.commit()
        finally:
            release.set()
        result = future.result(timeout=10)
    assert result["amount_minor"] == 1599


def test_concurrent_integrity_initializers_record_one_checksum(delivery):
    barrier = Barrier(2)

    def worker(_):
        barrier.wait(timeout=10)
        return oap_eats_store.init_schema(assume_yes=True)["integrity_checksum"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(worker, (0, 1))) == [oap_eats_store.INTEGRITY_MIGRATION_CHECKSUM] * 2
    with postgres_db.connect(readonly=True) as db:
        assert db.execute("SELECT count(*) FROM oap_schema_migrations WHERE version=%s", (oap_eats_store.INTEGRITY_MIGRATION_VERSION,)).fetchone()[0] == 1


@pytest.mark.parametrize("missing", [True, False])
def test_integrity_receipt_cannot_hide_schema_drift(delivery, missing):
    oap_eats_store.init_schema(assume_yes=True)
    with postgres_db.connect() as db:
        db.execute("ALTER TABLE oap_eats_orders DROP COLUMN pricing_version")
        if not missing:
            db.execute("ALTER TABLE oap_eats_orders ADD COLUMN pricing_version INTEGER")
        db.commit()
    with pytest.raises(RuntimeError, match="schema mismatch"):
        oap_eats_store.init_schema(assume_yes=True)


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


@pytest.mark.parametrize("statement,key,error", [
    ("UPDATE oap_sika_payment_intents SET status='CANCELLED' WHERE payment_id=%s", "intent", "payment_intent_not_bindable"),
    ("UPDATE oap_sika_payment_intents SET amount=1 WHERE payment_id=%s", "intent", "payment_amount_mismatch"),
    ("UPDATE oap_sika_payment_intents SET currency='USD' WHERE payment_id=%s", "intent", "payment_currency_mismatch"),
    ("UPDATE oap_sika_payment_intents SET payer_account_id='other' WHERE payment_id=%s", "intent", "payment_payer_binding_changed"),
    ("DELETE FROM oap_sika_payment_intents WHERE payment_id=%s", "intent", "payment_intent_not_found"),
    ("UPDATE oap_sika_payment_holds SET status='RELEASED' WHERE hold_id=%s", "hold", "active_payment_hold_required"),
    ("UPDATE oap_sika_payment_holds SET amount=1 WHERE hold_id=%s", "hold", "payment_amount_mismatch"),
    ("UPDATE oap_sika_payment_holds SET currency='USD' WHERE hold_id=%s", "hold", "payment_currency_mismatch"),
    ("UPDATE oap_sika_payment_holds SET payer_account_id='other' WHERE hold_id=%s", "hold", "payment_hold_binding_mismatch"),
    ("UPDATE oap_sika_payment_holds SET hold_id='replacement' WHERE hold_id=%s", "hold", "payment_hold_binding_mismatch"),
    ("DELETE FROM oap_sika_payment_holds WHERE hold_id=%s", "hold", "active_payment_hold_required"),
])
def test_payment_write_rejects_evidence_changed_after_preflight(
    delivery, payment, monkeypatch, statement, key, error,
):
    original = oap_eats_store.STORE.bind_payment

    def change_then_bind(**kwargs):
        with postgres_db.connect() as db:
            db.execute(statement, (payment[key],))
            db.commit()
        return original(**kwargs)

    monkeypatch.setattr(oap_eats_store.STORE, "bind_payment", change_then_bind)
    with pytest.raises(ValueError, match=error):
        _bind_payment(delivery, payment)
    assert _order_readback(delivery) == ("authorised", None, None, 0)


def test_binding_response_uses_locked_intent_status(delivery, payment, monkeypatch):
    original = oap_eats_store.STORE.bind_payment

    def submit_then_bind(**kwargs):
        with postgres_db.connect() as db:
            db.execute("UPDATE oap_sika_payment_intents SET status='SUBMITTED' WHERE payment_id=%s", (payment["intent"],))
            db.commit()
        return original(**kwargs)

    monkeypatch.setattr(oap_eats_store.STORE, "bind_payment", submit_then_bind)
    result = _bind_payment(delivery, payment)
    assert result["payment_status"] == "SUBMITTED"
    assert result["payment_captured"] is result["money_moved_by_eats"] is False


def _second_order(delivery):
    order = str(uuid4())
    with postgres_db.connect() as db:
        db.execute(
            """INSERT INTO oap_eats_orders(order_id,customer_identity_id,merchant_id,
                   state,items,amount_minor,currency,fulfilment_mode,idempotency_key)
               VALUES (%s,%s,%s,'authorised','[]',1599,'GBP','delivery',%s)""",
            (order, delivery["customer_identity_id"], delivery["merchant"], "order-" + order),
        )
        db.execute("UPDATE oap_eats_orders SET pricing_version=%s WHERE order_id=%s", (oap_eats_store.PRICING_VERSION, order))
        db.commit()
    return {**delivery, "order_id": order}


@pytest.mark.parametrize("same_order", [True, False])
def test_payment_retry_or_cross_order_reuse(delivery, payment, same_order):
    first = _bind_payment(delivery, payment)
    target = delivery if same_order else _second_order(delivery)
    if same_order:
        assert _bind_payment(target, payment) == first
        assert _order_readback(target) == ("authorised", payment["intent"], payment["hold"], 1)
    else:
        with pytest.raises(PermissionError, match="payment_already_bound_to_order"):
            _bind_payment(target, payment)
        assert _order_readback(target) == ("authorised", None, None, 0)


@pytest.mark.parametrize("same_order", [True, False])
def test_competing_payment_binds_have_one_durable_event(delivery, payment, same_order):
    target = delivery if same_order else _second_order(delivery)
    barrier = Barrier(2)

    def worker(order):
        barrier.wait(timeout=10)
        try:
            return _bind_payment(order, payment)["order_id"]
        except PermissionError as exc:
            assert str(exc) == "payment_already_bound_to_order"
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, [delivery, target]))
    assert results.count(None) == (0 if same_order else 1)
    with postgres_db.connect(readonly=True) as db:
        assert db.execute("SELECT count(*) FROM oap_eats_orders WHERE payment_id=%s", (payment["intent"],)).fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM oap_eats_order_events").fetchone()[0] == 1


@pytest.mark.parametrize("concurrent", [False, True])
def test_order_cannot_switch_to_another_valid_payment(delivery, payment, concurrent):
    other = _seed_payment(delivery)
    barrier = Barrier(2)

    def worker(candidate):
        if concurrent:
            barrier.wait(timeout=10)
        try:
            return _bind_payment(delivery, candidate)["payment_id"]
        except PermissionError as exc:
            assert str(exc) == "order_payment_binding_denied"
            return None

    if concurrent:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, [payment, other]))
    else:
        results = [worker(payment), worker(other)]
    winner = next(result for result in results if result is not None)
    winner_hold = payment["hold"] if winner == payment["intent"] else other["hold"]
    assert results.count(None) == 1
    assert _order_readback(delivery) == ("authorised", winner, winner_hold, 1)
    with postgres_db.connect(readonly=True) as db:
        assert db.execute("SELECT status FROM oap_sika_payment_intents").fetchall() == [("AUTHORISED",), ("AUTHORISED",)]
        assert db.execute("SELECT status FROM oap_sika_payment_holds").fetchall() == [("ACTIVE",), ("ACTIVE",)]


@pytest.mark.parametrize("field,key", [("payment_id", "intent"), ("payment_hold_id", "hold")])
def test_existing_partial_binding_blocks_reuse(delivery, payment, field, key):
    other = _second_order(delivery)
    with postgres_db.connect() as db:
        db.execute(
            sql.SQL("UPDATE oap_eats_orders SET {}=%s WHERE order_id=%s").format(sql.Identifier(field)),
            (payment[key], other["order_id"]),
        )
        db.commit()
    with pytest.raises(PermissionError, match="payment_already_bound_to_order"):
        _bind_payment(delivery, payment)
    assert _order_readback(delivery) == ("authorised", None, None, 0)


@pytest.mark.parametrize("field,key", [("hold_id", "hold"), ("payer_account_id", "account")])
def test_direct_store_call_cannot_supply_unrelated_evidence(delivery, payment, field, key):
    args = {"order_id": delivery["order_id"], "customer_identity_id": delivery["customer_identity_id"],
            "payment_id": payment["intent"], "hold_id": payment["hold"], "payer_account_id": payment["account"]}
    args[field] = "unrelated-" + payment[key]
    with pytest.raises((ValueError, PermissionError)):
        oap_eats_store.STORE.bind_payment(**args)
    assert _order_readback(delivery) == ("authorised", None, None, 0)


@pytest.mark.parametrize("after_event", [False, True])
def test_payment_event_failure_rolls_back_binding(delivery, payment, monkeypatch, after_event):
    connect = postgres_db.connect

    class FailingConnection:
        def __init__(self, db):
            self.db = db

        def execute(self, statement, *args):
            is_event = "INSERT INTO oap_eats_order_events" in str(statement)
            if is_event and not after_event:
                raise RuntimeError("injected_payment_event_failure")
            result = self.db.execute(statement, *args)
            if is_event:
                raise RuntimeError("injected_payment_event_failure")
            return result

        def commit(self):
            self.db.commit()

    @contextmanager
    def failing_connect(*, readonly=False):
        with connect(readonly=readonly) as db:
            yield db if readonly else FailingConnection(db)

    with monkeypatch.context() as patch:
        patch.setattr(postgres_db, "connect", failing_connect)
        with pytest.raises(RuntimeError, match="injected_payment_event_failure"):
            _bind_payment(delivery, payment)
    assert _order_readback(delivery) == ("authorised", None, None, 0)
    _bind_payment(delivery, payment)
    assert _order_readback(delivery) == ("authorised", payment["intent"], payment["hold"], 1)


@pytest.mark.parametrize("statement,key", [
    ("UPDATE oap_sika_accounts SET status='CLOSED' WHERE account_id=%s", "account"),
    ("UPDATE oap_sika_accounts SET status='CLOSED' WHERE account_id=%s", "payee"),
    ("UPDATE oap_eats_merchants SET active=FALSE WHERE merchant_id=%s", "merchant"),
    ("UPDATE oap_sika_payment_intents SET status='CANCELLED' WHERE payment_id=%s", "intent"),
    ("UPDATE oap_sika_payment_holds SET status='RELEASED' WHERE hold_id=%s", "hold"),
])
def test_binding_locks_canonical_evidence_until_commit(delivery, payment, monkeypatch, statement, key):
    connect = postgres_db.connect
    locked, release = Event(), Event()

    class PausedConnection:
        def __init__(self, db):
            self.db = db

        def execute(self, query, *args):
            if "UPDATE oap_eats_orders" in str(query):
                locked.set()
                assert release.wait(timeout=10)
            return self.db.execute(query, *args)

        def commit(self):
            self.db.commit()

    @contextmanager
    def paused_connect(*, readonly=False):
        with connect(readonly=readonly) as db:
            yield db if readonly else PausedConnection(db)

    monkeypatch.setattr(postgres_db, "connect", paused_connect)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_bind_payment, delivery, payment)
        try:
            assert locked.wait(timeout=10)
            # This is a second real database connection. A competing state
            # change cannot pass the final checks and precede the binding commit.
            with pytest.raises(errors.LockNotAvailable), connect() as db:
                db.execute("SET LOCAL lock_timeout = '250ms'")
                db.execute(statement, (payment[key],))
                db.commit()
        finally:
            release.set()
        result = future.result(timeout=10)
    assert result["payment_status"] == "AUTHORISED"
    assert result["hold_status"] == "ACTIVE"
    assert _order_readback(delivery) == ("authorised", payment["intent"], payment["hold"], 1)


def _cancel(delivery, actor=None):
    return oap_eats_store.STORE.transition(
        order_id=delivery["order_id"], actor_identity_id=actor or delivery["customer_identity_id"], target_state="cancelled",
    )


def _delivery_snapshot(delivery):
    return oap_eats_store.STORE.read_delivery(order_id=delivery["order_id"], customer_identity_id=delivery["customer_identity_id"])


def _match_fixture(delivery, booking):
    worker, proposal = delivery["outsider"], str(uuid4())
    with postgres_db.connect() as db:
        db.execute("INSERT INTO oap_identity_roles(identity_id,role_id) VALUES (%s,'MOVEMENT_COURIER') ON CONFLICT DO NOTHING", (worker,))
        db.execute("INSERT INTO oap_movement_availability(identity_id,role_type,availability_state) VALUES (%s,'courier','ONLINE') ON CONFLICT DO NOTHING", (worker,))
        db.execute("INSERT INTO oap_movement_match_proposals(proposal_id,booking_id,worker_identity_id,worker_role,score,reason) VALUES (%s,%s,%s,'courier',1,'CI fixture')", (proposal, booking, worker))
        db.execute("UPDATE oap_movement_bookings SET state='MATCH_PROPOSED' WHERE booking_id=%s", (booking,))
        db.commit()
    return {"proposal_id": proposal, "worker_identity_id": worker}


@pytest.mark.parametrize("service", ["ride", "delivery", "ebike"])
def test_shared_engine_mints_one_durable_journey_per_booking(delivery, service):
    args = {"member_identity_id": delivery["customer_identity_id"], "service_type": service,
            "pickup": delivery["pickup"], "destination": delivery["destination"],
            "idempotency_key": "journey-" + delivery["order_id"]}
    first = movement_operations.STORE.create_booking(**args)
    assert movement_operations.PostgresMovementStore().create_booking(**args) == first
    read = global_journey_store.read_journey(journey_id=first["journey_id"], identity_id=delivery["customer_identity_id"])
    assert read["booking_id"] == first["booking_id"]
    assert read["service_type"] == service
    assert read["external_dispatch_performed"] is read["payment_performed"] is False
    for actor in (delivery["merchant"], delivery["outsider"]):
        assert global_journey_store.read_journey(journey_id=first["journey_id"], identity_id=actor) is None
        assert movement_operations.STORE.get_booking(booking_id=first["booking_id"], identity_id=actor) is None
    cancelled = movement_operations.STORE.cancel_booking(booking_id=first["booking_id"], member_identity_id=delivery["customer_identity_id"])
    assert movement_operations.STORE.cancel_booking(booking_id=first["booking_id"], member_identity_id=delivery["customer_identity_id"]) == cancelled
    assert global_journey_store.read_journey(journey_id=first["journey_id"], identity_id=delivery["customer_identity_id"])["state"] == "CANCELLED"
    with postgres_db.connect(readonly=True) as db:
        assert db.execute("SELECT count(*) FROM oap_global_journey_associations").fetchone()[0] == 1


def test_eats_readback_verifies_each_durable_owner_and_replay_has_one_event(delivery):
    first = _create(delivery)
    assert _create(delivery) == first
    snapshot = _delivery_snapshot(delivery)
    assert snapshot["journey_id"] == first["movement"]["journey_id"]
    assert snapshot["movement_booking_id"] == first["movement_booking_id"]
    assert _order_readback(delivery)[3] == 1
    for actor in (delivery["merchant"], delivery["outsider"]):
        with pytest.raises(PermissionError, match="order_delivery_not_verified"):
            oap_eats_store.STORE.read_delivery(order_id=delivery["order_id"], customer_identity_id=actor)


@pytest.mark.parametrize("change", ["booking_owner", "association_owner", "origin", "service", "unready_order"])
def test_delivery_binding_cannot_accept_unrelated_or_changed_evidence(delivery, change):
    first = _create(delivery)
    booking = first["movement_booking_id"]
    with postgres_db.connect() as db:
        if change == "booking_owner":
            db.execute("UPDATE oap_movement_bookings SET member_identity_id=%s WHERE booking_id=%s", (delivery["outsider"], booking))
        elif change == "association_owner":
            db.execute("UPDATE oap_global_journey_associations SET owner_identity_id=%s WHERE booking_id=%s", (delivery["outsider"], booking))
        elif change == "origin":
            db.execute("UPDATE oap_movement_bookings SET route_snapshot='{}' WHERE booking_id=%s", (booking,))
        elif change == "service":
            db.execute("UPDATE oap_movement_bookings SET service_type='ride' WHERE booking_id=%s", (booking,))
        else:
            db.execute("UPDATE oap_eats_orders SET state='created' WHERE order_id=%s", (delivery["order_id"],))
        db.commit()
    with pytest.raises(PermissionError):
        oap_eats_store.STORE.bind_movement(order_id=delivery["order_id"], customer_identity_id=delivery["customer_identity_id"], booking_id=booking)
    assert _order_readback(delivery)[3] == 1
    if change in {"booking_owner", "association_owner", "origin", "service"}:
        with pytest.raises(PermissionError):
            _delivery_snapshot(delivery)


@pytest.mark.parametrize("actor", ["customer_identity_id", "merchant"])
@pytest.mark.parametrize("accepted", [False, True])
def test_order_cancellation_commits_booking_proposals_consent_and_receipt(delivery, actor, accepted):
    first = _create(delivery)
    booking = first["movement_booking_id"]
    match = _match_fixture(delivery, booking)
    if accepted:
        movement_match_safety.STORE.accept_match(**match)
    movement_operations.STORE.grant_tracking_consent(booking_id=booking, identity_id=delivery["customer_identity_id"], expires_at=datetime.now(UTC) + timedelta(minutes=10))
    with postgres_db.connect() as db:
        db.execute("INSERT INTO oap_movement_trip_channels(booking_id,state) VALUES (%s,'READY')", (booking,))
        db.commit()
    first_cancel = _cancel(delivery, delivery[actor])
    assert _cancel(delivery, delivery[actor]) == first_cancel
    snapshot = _delivery_snapshot(delivery)
    assert snapshot["order_state"] == "cancelled"
    assert snapshot["booking_state"] == "CANCELLED"
    assert snapshot["cancelled_at"]
    assert _order_readback(delivery)[3] == 2
    with postgres_db.connect(readonly=True) as db:
        assert db.execute("SELECT state FROM oap_movement_match_proposals").fetchall() == [("EXPIRED",)]
        assert db.execute("SELECT state FROM oap_movement_tracking_consents").fetchall() == [("REVOKED",)]
        assert db.execute("SELECT state FROM oap_movement_trip_channels").fetchall() == [("CLOSED",)]
        assert db.execute("SELECT count(*) FROM oap_journey_cancellations").fetchone()[0] == 1
        if accepted:
            assert db.execute("SELECT availability_state FROM oap_movement_availability").fetchone()[0] == "OFFLINE"
    with pytest.raises(PermissionError):
        movement_match_safety.STORE.accept_match(**match)
    with pytest.raises(PermissionError):
        movement_operations.STORE.grant_tracking_consent(booking_id=booking, identity_id=delivery["customer_identity_id"], expires_at=datetime.now(UTC) + timedelta(minutes=10))
    with pytest.raises(PermissionError):
        movement_operations.STORE.record_tracking_point(booking_id=booking, identity_id=delivery["customer_identity_id"], latitude=51, longitude=0)


@pytest.mark.parametrize("state", ["IN_PROGRESS", "COMPLETED"])
def test_active_or_completed_booking_blocks_order_cancellation_atomically(delivery, state):
    first = _create(delivery)
    with postgres_db.connect() as db:
        db.execute("UPDATE oap_movement_bookings SET state=%s WHERE booking_id=%s", (state, first["movement_booking_id"]))
        db.commit()
    with pytest.raises(ValueError, match="booking_not_cancellable"):
        _cancel(delivery)
    assert _order_readback(delivery)[0] == "authorised"
    assert _delivery_snapshot(delivery)["booking_state"] == state


def test_product_cancel_cannot_be_bypassed_and_does_not_refund(delivery, payment):
    first = _create(delivery)
    _bind_payment(delivery, payment)
    with pytest.raises(PermissionError, match="cancel_through_product_required"):
        movement_operations.STORE.cancel_booking(booking_id=first["movement_booking_id"], member_identity_id=delivery["customer_identity_id"])
    _cancel(delivery)
    read = _delivery_snapshot(delivery)
    assert read["payment_action_required"] is True
    assert read["refund_performed"] is read["payment_captured"] is False
    with postgres_db.connect(readonly=True) as db:
        assert db.execute("SELECT status FROM oap_sika_payment_intents WHERE payment_id=%s", (payment["intent"],)).fetchone()[0] == "AUTHORISED"
        assert db.execute("SELECT status FROM oap_sika_payment_holds WHERE hold_id=%s", (payment["hold"],)).fetchone()[0] == "ACTIVE"


@pytest.mark.parametrize("operation", ["accept", "decline", "create", "cancel"])
def test_cancellation_races_cannot_reopen_or_orphan_a_delivery(delivery, operation):
    first = None if operation == "create" else _create(delivery)
    match = _match_fixture(delivery, first["movement_booking_id"]) if operation in {"accept", "decline"} else None
    barrier = Barrier(2)

    def worker(index):
        barrier.wait(timeout=10)
        try:
            if index == 0 or operation == "cancel":
                return _cancel(delivery)
            if operation == "create":
                return _create(delivery)
            return getattr(movement_match_safety.STORE, operation + "_match")(**match)
        except (PermissionError, ValueError) as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(worker, (0, 1)))
    assert _order_readback(delivery)[0] == "cancelled"
    with postgres_db.connect(readonly=True) as db:
        assert db.execute("SELECT count(*) FROM oap_movement_bookings WHERE state<>'CANCELLED'").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM oap_movement_match_proposals WHERE state IN ('PROPOSED','ACCEPTED')").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM oap_movement_availability WHERE availability_state='BUSY'").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM oap_global_journey_associations").fetchone()[0] == len(_readback(delivery)[0])


def test_cancellation_receipt_failure_rolls_back_every_state(delivery):
    first = _create(delivery)
    _match_fixture(delivery, first["movement_booking_id"])
    with postgres_db.connect() as db:
        db.execute("""CREATE FUNCTION reject_cancellation() RETURNS trigger LANGUAGE plpgsql AS $$
                     BEGIN RAISE EXCEPTION 'injected_cancellation_failure'; END $$""")
        db.execute("CREATE TRIGGER reject_cancellation BEFORE INSERT ON oap_journey_cancellations FOR EACH ROW EXECUTE FUNCTION reject_cancellation()")
        db.commit()
    with pytest.raises(errors.RaiseException):
        _cancel(delivery)
    assert _order_readback(delivery)[0] == "authorised"
    assert _delivery_snapshot(delivery)["booking_state"] == "MATCH_PROPOSED"
    with postgres_db.connect() as db:
        assert db.execute("SELECT state FROM oap_movement_match_proposals").fetchone()[0] == "PROPOSED"
        db.execute("DROP TRIGGER reject_cancellation ON oap_journey_cancellations")
        db.commit()
    _cancel(delivery)
    assert _delivery_snapshot(delivery)["booking_state"] == "CANCELLED"


@pytest.mark.parametrize("action", ["create", "cancel"])
@pytest.mark.parametrize("phase", ["before_commit", "after_commit"])
def test_sigkill_before_or_after_commit_recovers_one_linked_journey(delivery, action, phase):
    if action == "cancel":
        _create(delivery)
        args = {"order_id": delivery["order_id"], "actor_identity_id": delivery["customer_identity_id"], "target_state": "cancelled"}
    else:
        args = {key: value for key, value in delivery.items() if key not in {"merchant", "outsider"}}
    worker = Path(__file__).with_name("journey_crash_worker.py")
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
    process = subprocess.Popen([sys.executable, str(worker)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    try:
        process.stdin.write(json.dumps({"args": args, "phase": phase, "action": action}))
        process.stdin.close()
        ready, _, _ = select.select([process.stdout], [], [], 15)
        assert ready, "Crash worker did not reach its real commit boundary"
        marker = process.stdout.readline().strip()
        if marker != phase:
            raise AssertionError(process.stderr.read())
        process.kill()
        process.wait(timeout=10)
        assert process.returncode < 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        process.stdout.close()
        process.stderr.close()
    if action == "create":
        assert len(_readback(delivery)[0]) == (1 if phase == "after_commit" else 0)
        result = _create(delivery)
        assert _create(delivery) == result
    else:
        expected = "CANCELLED" if phase == "after_commit" else "REQUESTED"
        assert _delivery_snapshot(delivery)["booking_state"] == expected
        _cancel(delivery)
        assert _delivery_snapshot(delivery)["booking_state"] == "CANCELLED"
    with postgres_db.connect(readonly=True) as db:
        assert db.execute("SELECT count(*) FROM oap_movement_bookings").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM oap_global_journey_associations").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM oap_journey_cancellations").fetchone()[0] == (1 if action == "cancel" else 0)


def test_journey_migrations_record_both_checksums_without_changing_base(delivery):
    for _ in range(2):
        assert global_journey_schema.init_schema(assume_yes=True)["applied"] is True
    with postgres_db.connect(readonly=True) as db:
        assert db.execute("SELECT checksum FROM oap_schema_migrations WHERE version=%s", (global_journey_schema.LIFECYCLE_VERSION,)).fetchone()[0] == global_journey_schema.LIFECYCLE_CHECKSUM


@pytest.mark.parametrize("same_booking", [True, False])
def test_competing_acceptances_have_one_booking_per_worker_and_one_worker_per_booking(delivery, same_booking):
    first = _create(delivery)
    match1 = _match_fixture(delivery, first["movement_booking_id"])
    if same_booking:
        match2 = {"proposal_id": str(uuid4()), "worker_identity_id": delivery["merchant"]}
        with postgres_db.connect() as db:
            db.execute("INSERT INTO oap_identity_roles(identity_id,role_id) VALUES (%s,'MOVEMENT_COURIER')", (delivery["merchant"],))
            db.execute("INSERT INTO oap_movement_availability(identity_id,role_type,availability_state) VALUES (%s,'courier','ONLINE')", (delivery["merchant"],))
            db.execute("INSERT INTO oap_movement_match_proposals(proposal_id,booking_id,worker_identity_id,worker_role,score,reason) VALUES (%s,%s,%s,'courier',1,'CI')", (match2["proposal_id"], first["movement_booking_id"], delivery["merchant"]))
            db.commit()
    else:
        other = _second_order(delivery)
        second = _create(other, idempotency_key="second-" + other["order_id"])
        match2 = _match_fixture(delivery, second["movement_booking_id"])
        # A second available role must not bypass identity-level exclusivity.
        with postgres_db.connect() as db:
            db.execute("INSERT INTO oap_identity_roles(identity_id,role_id) VALUES (%s,'MOVEMENT_RIDER')", (delivery["outsider"],))
            db.execute("INSERT INTO oap_movement_availability(identity_id,role_type,availability_state) VALUES (%s,'rider','ONLINE')", (delivery["outsider"],))
            db.execute("UPDATE oap_movement_match_proposals SET worker_role='rider' WHERE proposal_id=%s", (match2["proposal_id"],))
            db.commit()
    barrier = Barrier(2)

    def worker(match):
        barrier.wait(timeout=10)
        try:
            return movement_match_safety.STORE.accept_match(**match)["state"]
        except PermissionError:
            return "DENIED"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(worker, (match1, match2))) == ["ACCEPTED", "DENIED"]
    with postgres_db.connect(readonly=True) as db:
        assert db.execute("SELECT count(*) FROM oap_movement_match_proposals WHERE state='ACCEPTED'").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM oap_movement_bookings WHERE state='ACCEPTED'").fetchone()[0] == 1


@pytest.mark.parametrize("state", ["SUSPENDED", "REVOKED", "missing"])
def test_journey_creation_requires_durable_active_owner_and_rolls_back(delivery, state):
    with postgres_db.connect() as db:
        if state == "missing":
            db.execute("DELETE FROM oap_identities WHERE identity_id=%s", (delivery["customer_identity_id"],))
        else:
            db.execute("UPDATE oap_identities SET status=%s WHERE identity_id=%s", (state, delivery["customer_identity_id"]))
        db.commit()
    with pytest.raises(PermissionError, match="journey_owner_required"):
        _create(delivery)
    assert _readback(delivery) == ([], None)
    with postgres_db.connect(readonly=True) as db:
        assert db.execute("SELECT count(*) FROM oap_global_journey_associations").fetchone()[0] == 0


def test_unverified_booking_core_intent_is_not_adopted(delivery):
    first = _create(delivery)
    with postgres_db.connect() as db:
        db.execute("UPDATE oap_global_journey_associations SET intent_id=%s WHERE booking_id=%s", ("oap-book-" + "a" * 16, first["movement_booking_id"]))
        db.commit()
    assert global_journey_store.read_journey(journey_id=first["movement"]["journey_id"], identity_id=delivery["customer_identity_id"]) is None
    with pytest.raises(PermissionError, match="intent_owner_evidence_required"):
        _create(delivery)
    with pytest.raises(PermissionError):
        _delivery_snapshot(delivery)


@pytest.mark.parametrize("accepted", [False, True])
def test_worker_cannot_cancel_customer_product(delivery, accepted):
    first = _create(delivery)
    match = _match_fixture(delivery, first["movement_booking_id"])
    if accepted:
        movement_match_safety.STORE.accept_match(**match)
    with pytest.raises(PermissionError, match="order_not_owned"):
        _cancel(delivery, delivery["outsider"])
    with pytest.raises(PermissionError, match="booking_not_found"):
        movement_operations.STORE.cancel_booking(booking_id=first["movement_booking_id"], member_identity_id=delivery["outsider"])
    assert _delivery_snapshot(delivery)["order_state"] == "authorised"
