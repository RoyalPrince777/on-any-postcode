from datetime import UTC, datetime, timedelta

from mission_control import postgres_db, travel_supply_core
from oap.smi import travel_agency


VALID_ID = "11111111-1111-4111-8111-111111111111"


def _assert_raises(exception_type, message, callback, *args, **kwargs):
    try:
        callback(*args, **kwargs)
    except exception_type as exc:
        assert message in str(exc)
    else:
        raise AssertionError(f"Expected {exception_type.__name__}: {message}")


def _base_not_ready(monkeypatch):
    monkeypatch.setattr(
        postgres_db,
        "postgres_status",
        lambda: {"configured": False, "initialized": False},
    )


def test_supply_core_is_first_party_without_new_world_agent_or_brain(monkeypatch):
    _base_not_ready(monkeypatch)
    current = travel_supply_core.status()

    assert current["component"] == "OAP Supply Core"
    assert current["software_ready"] is True
    assert current["schema_ready"] is False
    assert current["creates_intelligence_worlds"] is False
    assert current["creates_agents"] is False
    assert current["creates_brain"] is False
    assert current["external_provider_authority"] is False
    assert current["human_authority_final"] is True
    assert current["payment_capture_live"] is False
    assert current["pass_issuance_live"] is False
    assert current["commission_settlement_live"] is False


def test_supply_core_schema_is_explicit_checksum_gated_and_non_destructive(monkeypatch):
    assert travel_supply_core.SUPPLY_CORE_MIGRATION_VERSION == "0007_oap_supply_core"
    assert travel_supply_core.SUPPLY_CORE_TABLES == {
        "oap_supply_suppliers",
        "oap_supply_listings",
        "oap_supply_inventory_slots",
        "oap_supply_reservation_holds",
        "oap_supply_reservations",
    }
    sql = "\n".join(travel_supply_core.SUPPLY_CORE_SCHEMA_STATEMENTS)
    assert "oap_market_items" not in sql
    assert "oap_market_orders" not in sql
    assert "oap_commerce_orders" not in sql
    assert "payment_state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'" in sql
    assert "pass_state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'" in sql
    assert "commission_state TEXT NOT NULL DEFAULT 'PROVIDER_REQUIRED'" in sql
    assert len(travel_supply_core.SUPPLY_CORE_MIGRATION_CHECKSUM) == 64

    _assert_raises(
        RuntimeError,
        "Explicit human approval required",
        travel_supply_core.init_supply_core_schema,
    )

    monkeypatch.setattr(postgres_db, "postgres_status", lambda: {"initialized": True})
    dry_run = travel_supply_core.init_supply_core_schema(
        assume_yes=True,
        dry_run=True,
    )
    assert dry_run["migration"] == "0007_oap_supply_core"
    assert dry_run["tables"] == 5


def test_supplier_certification_requires_human_authority():
    store = travel_supply_core.PostgresTravelSupplyStore()

    _assert_raises(
        PermissionError,
        "human_authority_approval_required",
        store.certify_supplier,
        supplier_id=VALID_ID,
        human_authority_approved=False,
    )


def test_input_validation_fails_before_any_database_write():
    store = travel_supply_core.PostgresTravelSupplyStore()

    _assert_raises(
        ValueError,
        "invalid_supplier_type",
        store.create_supplier,
        owner_identity_id=VALID_ID,
        display_name="Example",
        supplier_type="not-real",
    )

    _assert_raises(
        ValueError,
        "inventory_window_invalid",
        store.set_inventory_slot,
        owner_identity_id=VALID_ID,
        listing_id=VALID_ID,
        starts_at=datetime.now(UTC),
        ends_at=datetime.now(UTC) - timedelta(hours=1),
        capacity_total=1,
        price_minor=1000,
        currency="GBP",
        price_basis="per person",
    )

    future = datetime.now(UTC) + timedelta(days=1)
    _assert_raises(
        ValueError,
        "invalid_currency",
        store.set_inventory_slot,
        owner_identity_id=VALID_ID,
        listing_id=VALID_ID,
        starts_at=future,
        ends_at=future + timedelta(hours=1),
        capacity_total=1,
        price_minor=1000,
        currency="POUNDS",
        price_basis="per person",
    )


def test_travel_agency_exposes_oap_direct_marketplace_without_false_live_claims(
    monkeypatch,
):
    _base_not_ready(monkeypatch)
    current = travel_agency.status()

    assert current["oap_supply_core_software_ready"] is True
    assert current["oap_supply_core_schema_ready"] is False
    assert current["oap_owns_direct_supplier_inventory_system"] is True
    assert current["oap_owns_external_supplier_inventory"] is False
    assert current["direct_live_supply_ready"] is False
    assert current["certified_direct_supplier_count"] == 0
    assert current["live_direct_inventory_slot_count"] == 0
    assert current["payment_transactions_live"] is False
    assert current["pass_issuance_live"] is False
    assert current["commission_settlement_live"] is False

    gate_states = {gate["id"]: gate["ready"] for gate in current["gates"]}
    assert gate_states["oap_supply_core_software"] is True
    assert gate_states["oap_supply_core_schema"] is False
