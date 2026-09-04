from oap.smi import travel_agency


def _clear_supply_env(monkeypatch):
    for suffix in (
        "CONNECTED",
        "SEARCH_CERTIFIED",
        "COMMERCIAL_TERMS_CERTIFIED",
        "BOOKING_CERTIFIED",
    ):
        monkeypatch.delenv(f"OAP_SUPPLY_BOOKING_COM_{suffix}", raising=False)


def _supply_modules():
    travel_supply_core = __import__(
        "mission_control.travel_supply_core",
        fromlist=["travel_supply_core"],
    )
    postgres_db = __import__("mission_control.postgres_db", fromlist=["postgres_db"])
    return travel_supply_core, postgres_db


def _assert_raises(exception_type, message, callback, *args, **kwargs):
    try:
        callback(*args, **kwargs)
    except exception_type as exc:
        assert message in str(exc)
    else:
        raise AssertionError(f"Expected {exception_type.__name__}: {message}")


def test_travel_agency_preserves_smi_boundaries(monkeypatch):
    _clear_supply_env(monkeypatch)
    current = travel_agency.status()

    assert current["intelligence_world"] is False
    assert current["agent"] is False
    assert current["brain"] is False
    assert current["brain_count_added"] == 0
    assert current["capability_registry_ready"] is True
    assert current["supply_adapter_framework_ready"] is True
    assert current["provider_authority"] is False
    assert current["guardian_gate_required"] is True
    assert current["human_authority_final"] is True


def test_travel_agency_keeps_transactions_fail_closed_without_direct_supply(monkeypatch):
    _clear_supply_env(monkeypatch)
    current = travel_agency.status()

    assert current["live_supply_search_ready"] is False
    assert current["external_live_supply_ready"] is False
    assert current["external_lookup_persisted"] is False
    assert current["booking_transactions_live"] is False
    assert current["payment_transactions_live"] is False
    assert current["commission_settlement_live"] is False
    assert current["production_booking_claim_allowed"] is False
    assert current["production_payment_claim_allowed"] is False
    assert current["production_commission_claim_allowed"] is False

    gate_states = {gate["id"]: gate["ready"] for gate in current["gates"]}
    assert gate_states["capability_registry"] is True
    assert gate_states["external_lookup_framework"] is True
    assert gate_states["live_direct_supply"] is False
    assert gate_states["booking_execution"] is False
    assert gate_states["payment_execution"] is False
    assert gate_states["commission_settlement"] is False


def test_connected_external_lookup_does_not_become_oap_supply_or_booking(monkeypatch):
    monkeypatch.setenv("OAP_SUPPLY_BOOKING_COM_CONNECTED", "1")
    monkeypatch.setenv("OAP_SUPPLY_BOOKING_COM_SEARCH_CERTIFIED", "1")
    monkeypatch.setenv("OAP_SUPPLY_BOOKING_COM_COMMERCIAL_TERMS_CERTIFIED", "1")
    monkeypatch.setenv("OAP_SUPPLY_BOOKING_COM_BOOKING_CERTIFIED", "1")

    current = travel_agency.status()

    assert current["runtime_external_search_ready"] is True
    assert current["external_lookup_mode"] == "on_demand_only"
    assert current["external_lookup_persisted"] is False
    assert current["live_supply_search_ready"] is False
    assert current["external_live_supply_ready"] is False
    assert current["booking_transactions_live"] is False
    assert current["payment_transactions_live"] is False
    assert current["commission_settlement_live"] is False


def test_supply_core_is_first_party_without_new_world_agent_or_brain(monkeypatch):
    travel_supply_core, postgres_db = _supply_modules()
    monkeypatch.setattr(
        postgres_db,
        "postgres_status",
        lambda: {"configured": False, "initialized": False},
    )
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
    travel_supply_core, postgres_db = _supply_modules()

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


def test_supply_core_supplier_certification_requires_human_authority():
    travel_supply_core, _ = _supply_modules()
    store = travel_supply_core.PostgresTravelSupplyStore()

    _assert_raises(
        PermissionError,
        "human_authority_approval_required",
        store.certify_supplier,
        supplier_id="11111111-1111-4111-8111-111111111111",
        human_authority_approved=False,
    )


def test_supply_core_input_validation_fails_before_database_write():
    travel_supply_core, _ = _supply_modules()
    store = travel_supply_core.PostgresTravelSupplyStore()
    identity = "11111111-1111-4111-8111-111111111111"

    _assert_raises(
        ValueError,
        "invalid_supplier_type",
        store.create_supplier,
        owner_identity_id=identity,
        display_name="Example",
        supplier_type="not-real",
    )
    _assert_raises(
        ValueError,
        "inventory_window_invalid",
        store.set_inventory_slot,
        owner_identity_id=identity,
        listing_id=identity,
        starts_at="2026-09-05T12:00:00+00:00",
        ends_at="2026-09-05T11:00:00+00:00",
        capacity_total=1,
        price_minor=1000,
        currency="GBP",
        price_basis="per person",
    )
    _assert_raises(
        ValueError,
        "invalid_currency",
        store.set_inventory_slot,
        owner_identity_id=identity,
        listing_id=identity,
        starts_at="2026-09-05T12:00:00+00:00",
        ends_at="2026-09-05T13:00:00+00:00",
        capacity_total=1,
        price_minor=1000,
        currency="POUNDS",
        price_basis="per person",
    )


def test_travel_agency_exposes_direct_marketplace_without_false_live_claims(monkeypatch):
    _, postgres_db = _supply_modules()
    monkeypatch.setattr(
        postgres_db,
        "postgres_status",
        lambda: {"configured": False, "initialized": False},
    )
    current = travel_agency.status()

    assert current["oap_supply_core_software_ready"] is True
    assert current["oap_supply_core_schema_ready"] is False
    assert current["oap_owns_direct_supplier_inventory_system"] is True
    assert current["oap_owns_supplier_inventory"] is False
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
