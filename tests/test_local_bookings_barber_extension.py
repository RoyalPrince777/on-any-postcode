"""Barber appointments extend OAP Direct without rewriting event migrations."""

import hashlib

import pytest

from mission_control import (
    local_booking_extension,
    travel_marketplace,
    travel_supply_core,
)


def _extension_ready(monkeypatch, ready):
    monkeypatch.setattr(
        local_booking_extension,
        "schema_status",
        lambda: {"schema_ready": ready},
    )


def test_original_direct_migration_stays_unchanged():
    sql = "\n".join(travel_supply_core.SUPPLY_CORE_SCHEMA_STATEMENTS)
    assert "barber" not in sql
    assert "personal_service" not in sql
    assert travel_supply_core.SUPPLY_CORE_MIGRATION_VERSION == "0007_oap_supply_core"
    assert hashlib.sha256(sql.encode()).hexdigest() == travel_supply_core.SUPPLY_CORE_MIGRATION_CHECKSUM
    assert {"event", "barber"} <= travel_supply_core.SUPPLY_CATEGORIES
    assert "personal_service" in travel_supply_core.SUPPLIER_TYPES
    assert len(local_booking_extension.BARBER_EXTENSION_CHECKSUM) == 64


def test_barber_migration_is_human_gated_and_dry_run_never_writes(monkeypatch):
    with pytest.raises(RuntimeError, match="Explicit Human Authority approval required"):
        local_booking_extension.init_schema()
    monkeypatch.setattr(
        travel_supply_core,
        "supply_core_schema_status",
        lambda: {"schema_ready": False},
    )
    with pytest.raises(RuntimeError, match="Verified OAP Direct supply core required"):
        local_booking_extension.init_schema(assume_yes=True)
    monkeypatch.setattr(
        travel_supply_core,
        "supply_core_schema_status",
        lambda: {"schema_ready": True},
    )

    def no_db(*a, **k):
        raise AssertionError("dry run must not read or write PostgreSQL")

    monkeypatch.setattr(local_booking_extension.postgres_db, "connect", no_db)
    proof = local_booking_extension.init_schema(assume_yes=True, dry_run=True)
    assert proof["dry_run"] is True
    assert proof["statement_count"] == 4


def test_barber_discovery_does_not_claim_inventory_without_schema(monkeypatch):
    monkeypatch.setattr(
        travel_supply_core,
        "supply_core_schema_status",
        lambda: {"schema_ready": True},
    )
    _extension_ready(monkeypatch, False)

    def no_db(*a, **k):
        raise AssertionError("missing extension must not execute offer query")

    monkeypatch.setattr(travel_marketplace.postgres_db, "connect", no_db)
    response = travel_marketplace.public_offers(category="barber")
    assert response["ready"] is False
    assert response["offers"] == []
    assert response["count"] == 0
    assert response["error"] == "barber_extension_not_ready"


def test_barber_and_personal_service_writes_fail_before_database(monkeypatch):
    _extension_ready(monkeypatch, False)
    store = travel_supply_core.PostgresTravelSupplyStore()

    def no_db(*a, **k):
        raise AssertionError("unmigrated barber write reached PostgreSQL")

    monkeypatch.setattr(travel_supply_core.postgres_db, "connect", no_db)
    with pytest.raises(RuntimeError, match="barber_extension_not_ready"):
        store.create_supplier(
            owner_identity_id="11111111-1111-4111-8111-111111111111",
            display_name="Barber owner (not onboarded)",
            supplier_type="personal_service",
        )
    with pytest.raises(RuntimeError, match="barber_extension_not_ready"):
        store.create_listing(
            owner_identity_id="11111111-1111-4111-8111-111111111111",
            supplier_id="22222222-2222-4222-8222-222222222222",
            category="barber",
            title="Haircut",
            place_label="Mitcham",
            country="United Kingdom",
            idempotency_key="barber-uncertified-123",
        )


class _Rows:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class _Db:
    def __init__(self):
        self.statements = []
        self.receipt = None
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        self.statements.append((sql, params))
        if "SELECT checksum FROM oap_schema_migrations" in sql:
            return _Rows((self.receipt,) if self.receipt is not None else None)
        if "pg_get_constraintdef" in sql:
            field = params[0]
            return _Rows((
                "CHECK (category IN (...))"
                if "listings" in field
                else "CHECK (supplier_type IN (...))",
            ))
        if "INSERT INTO oap_schema_migrations" in sql:
            self.receipt = params[1]
        return _Rows()

    def commit(self):
        self.commits += 1


def test_barber_extension_additive_migration_has_receipt_and_no_seed(monkeypatch):
    monkeypatch.setattr(
        travel_supply_core,
        "supply_core_schema_status",
        lambda: {"schema_ready": True},
    )
    db = _Db()
    monkeypatch.setattr(local_booking_extension.postgres_db, "connect", lambda **kw: db)
    state = local_booking_extension.init_schema(assume_yes=True)
    assert state["schema_ready"] is True
    assert db.commits == 1
    statements = [sql for sql, _ in db.statements]
    assert any("oap_supply_listings_category_check" in sql for sql in statements)
    assert any("oap_supply_suppliers_supplier_type_check" in sql for sql in statements)
    assert all("INSERT INTO oap_supply_" not in sql for sql in statements)
    assert all("oap_supply_reservations" not in sql for sql in statements)
    second = local_booking_extension.init_schema(assume_yes=True)
    assert second["schema_ready"] is True
    assert db.commits == 1


def test_source_extension_status_is_honest_before_migration(monkeypatch):
    monkeypatch.setattr(
        travel_supply_core,
        "supply_core_schema_status",
        lambda: {"schema_ready": True},
    )
    db = _Db()
    monkeypatch.setattr(local_booking_extension.postgres_db, "connect", lambda **kw: db)
    status = local_booking_extension.schema_status()
    assert status["schema_ready"] is False
    assert status["trial_started"] is False
    assert status["payment_enabled"] is False
    assert status["supplier_confirmation_required"] is True


def test_existing_event_category_remains_bookable_separately(monkeypatch):
    monkeypatch.setattr(
        travel_supply_core,
        "supply_core_schema_status",
        lambda: {"schema_ready": True},
    )
    _extension_ready(monkeypatch, False)

    class _EmptyConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, sql, params):
            assert "l.category=%s" in sql
            assert "event" in params

            class _Results:
                def fetchall(self):
                    return []

            return _Results()

    monkeypatch.setattr(
        travel_marketplace.postgres_db,
        "connect",
        lambda readonly=False: _EmptyConn(),
    )
    result = travel_marketplace.public_offers(category="event")
    assert result["ready"] is True
    assert result["count"] == 0
