"""Ephemeral PostgreSQL proof of Eats ownership and atomic Movement binding.

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
