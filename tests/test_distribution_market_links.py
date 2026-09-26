from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from mission_control import distribution_market_links as links


class Result:
    def __init__(self, one=None, many=None):
        self.one = one
        self.many = [] if many is None else many

    def fetchone(self):
        return self.one

    def fetchall(self):
        return self.many


class Connection:
    def __init__(self, *, owner_ok=True, existing=None, read_row=None):
        self.owner_ok = owner_ok
        self.existing = [] if existing is None else existing
        self.read_row = read_row
        self.commands = []
        self.commits = 0

    def execute(self, sql, params=None):
        self.commands.append((sql, params))
        if "FROM oap_commerce_orders" in sql:
            return Result((1,) if self.owner_ok else None)
        if "FROM oap_movement_bookings" in sql:
            return Result((1,) if self.owner_ok else None)
        if "FROM oap_post_office_parcels" in sql:
            return Result((1,) if self.owner_ok else None)
        if "FROM oap_distribution_market_links" in sql and "FOR UPDATE" in sql:
            return Result(many=self.existing)
        if "FROM oap_distribution_market_links" in sql:
            return Result(one=self.read_row)
        return Result()

    def commit(self):
        self.commits += 1

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def install_connection(monkeypatch, connection):
    monkeypatch.setattr(
        links.postgres_db,
        "connect",
        lambda readonly=False: connection,
    )


def ids():
    return tuple(str(uuid4()) for _ in range(4))


def test_schema_references_existing_canonical_owners_only():
    sql = "\n".join(links.LINK_SCHEMA_STATEMENTS)
    assert "oap_commerce_orders(order_id)" in sql
    assert "oap_movement_bookings(booking_id)" in sql
    assert "oap_post_office_parcels(parcel_id)" in sql
    assert "owner_identity_id UUID NOT NULL REFERENCES users(id)" in sql
    assert "payment" not in sql.casefold()
    assert "dispatch" not in sql.casefold()


def test_schema_init_defaults_to_non_mutating_dry_run():
    with pytest.raises(RuntimeError, match="Explicit human approval"):
        links.init_link_schema()
    result = links.init_link_schema(assume_yes=True)
    assert result["dry_run"] is True
    assert len(result["checksum"]) == 64


def test_create_link_checks_all_three_canonical_owner_scopes(monkeypatch):
    owner, order, booking, parcel = ids()
    connection = Connection()
    install_connection(monkeypatch, connection)

    result = links.create_link(
        owner_identity_id=owner,
        order_id=order,
        booking_id=booking,
        parcel_id=parcel,
    )

    assert result["created"] is True
    assert result["payment_capture_performed"] is False
    assert result["dispatch_performed"] is False
    assert result["carrier_handoff_performed"] is False
    assert connection.commits == 1
    joined = "\n".join(sql for sql, _params in connection.commands)
    assert "buyer_identity_id=%s" in joined
    assert "member_identity_id=%s" in joined
    assert "owner_identity_id=%s" in joined


def test_create_link_fails_closed_on_owner_mismatch(monkeypatch):
    owner, order, booking, parcel = ids()
    connection = Connection(owner_ok=False)
    install_connection(monkeypatch, connection)

    with pytest.raises(PermissionError, match="canonical_owner_mismatch"):
        links.create_link(
            owner_identity_id=owner,
            order_id=order,
            booking_id=booking,
            parcel_id=parcel,
        )
    assert connection.commits == 0


def test_create_link_is_idempotent_for_same_tuple(monkeypatch):
    owner, order, booking, parcel = ids()
    connection = Connection(existing=[(order, booking, parcel)])
    install_connection(monkeypatch, connection)

    result = links.create_link(
        owner_identity_id=owner,
        order_id=order,
        booking_id=booking,
        parcel_id=parcel,
    )

    assert result["created"] is False
    assert connection.commits == 1
    assert not any(
        sql.lstrip().startswith("INSERT INTO oap_distribution_market_links")
        for sql, _params in connection.commands
    )


def test_create_link_rejects_reference_reuse(monkeypatch):
    owner, order, booking, parcel = ids()
    connection = Connection(existing=[(order, str(uuid4()), parcel)])
    install_connection(monkeypatch, connection)

    with pytest.raises(links.DistributionMarketLinkDenied, match="link_reference_reused"):
        links.create_link(
            owner_identity_id=owner,
            order_id=order,
            booking_id=booking,
            parcel_id=parcel,
        )


def test_stop_prevents_database_access(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("database accessed after STOP")

    monkeypatch.setattr(links.postgres_db, "connect", forbidden)
    owner, order, booking, parcel = ids()

    with pytest.raises(links.DistributionMarketLinkDenied, match="stopped"):
        links.create_link(
            owner_identity_id=owner,
            order_id=order,
            booking_id=booking,
            parcel_id=parcel,
            stopped=True,
        )


def test_owner_scoped_readback_never_claims_execution(monkeypatch):
    owner, order, booking, parcel = ids()
    created_at = datetime(2026, 9, 26, tzinfo=timezone.utc)
    connection = Connection(read_row=(order, booking, parcel, created_at))
    install_connection(monkeypatch, connection)

    result = links.read_link(owner_identity_id=owner, order_id=order)

    assert result["order_id"] == order
    assert result["booking_id"] == booking
    assert result["parcel_id"] == parcel
    assert result["payment_capture_performed"] is False
    assert result["dispatch_performed"] is False
    assert result["carrier_handoff_performed"] is False


def test_cross_owner_readback_fails_closed(monkeypatch):
    owner, order, _booking, _parcel = ids()
    connection = Connection(read_row=None)
    install_connection(monkeypatch, connection)

    with pytest.raises(PermissionError, match="canonical_link_not_owned"):
        links.read_link(owner_identity_id=owner, order_id=order)
