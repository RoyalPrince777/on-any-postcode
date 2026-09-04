from oap.smi import travel_agency


def _supply_modules():
    listing_media = __import__(
        "mission_control.listing_media",
        fromlist=["listing_media"],
    )
    travel_supply_core = __import__(
        "mission_control.travel_supply_core",
        fromlist=["travel_supply_core"],
    )
    postgres_db = __import__("mission_control.postgres_db", fromlist=["postgres_db"])
    return listing_media, travel_supply_core, postgres_db


def _assert_raises(exception_type, message, callback, *args, **kwargs):
    try:
        callback(*args, **kwargs)
    except exception_type as exc:
        assert message in str(exc)
    else:
        raise AssertionError(f"Expected {exception_type.__name__}: {message}")


def test_travel_agency_preserves_smi_boundaries():
    current = travel_agency.status()

    assert current["intelligence_world"] is False
    assert current["agent"] is False
    assert current["brain"] is False
    assert current["brain_count_added"] == 0
    assert current["capability_registry_ready"] is True
    assert current["supply_adapter_framework_ready"] is True
    assert current["external_provider_count"] == 0
    assert current["runtime_connected_external_provider_count"] == 0
    assert current["provider_authority"] is False
    assert current["guardian_gate_required"] is True
    assert current["human_authority_final"] is True


def test_external_marketplaces_never_make_oap_supply_live():
    current = travel_agency.status()

    assert current["external_supplier_catalogue_allowed"] is False
    assert current["external_data_fetch_allowed"] is True
    assert current["external_data_is_research_only"] is True
    assert current["external_live_supply_ready"] is False
    assert current["runtime_external_search_ready"] is False
    assert current["partner_snapshot_supply_ready"] is False
    assert current["active_partner_snapshot_count"] == 0
    assert current["live_partner_offer_count"] == 0


def test_supply_core_is_first_party_without_new_world_agent_or_brain(monkeypatch):
    _, travel_supply_core, postgres_db = _supply_modules()
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
    _, travel_supply_core, postgres_db = _supply_modules()

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
    dry_run = travel_supply_core.init_supply_core_schema(assume_yes=True, dry_run=True)
    assert dry_run["migration"] == "0007_oap_supply_core"
    assert dry_run["tables"] == 5


def test_listing_media_schema_is_explicit_and_rights_gated(monkeypatch):
    listing_media, _, postgres_db = _supply_modules()

    assert listing_media.LISTING_MEDIA_MIGRATION_VERSION == "0009_oap_supply_listing_photos"
    assert len(listing_media.LISTING_MEDIA_MIGRATION_CHECKSUM) == 64
    assert listing_media.MAX_IMAGE_BYTES == 2 * 1024 * 1024
    assert listing_media.MAX_PHOTOS_PER_LISTING == 8
    sql = "\n".join(listing_media.LISTING_MEDIA_SCHEMA_STATEMENTS)
    assert "oap_supply_listing_photos" in sql
    assert "rights_confirmed" in sql
    assert "BYTEA" in sql

    _assert_raises(RuntimeError, "Explicit human approval required", listing_media.init_schema)
    monkeypatch.setattr(postgres_db, "postgres_status", lambda: {"initialized": True})
    dry_run = listing_media.init_schema(assume_yes=True, dry_run=True)
    assert dry_run["migration"] == "0009_oap_supply_listing_photos"
    assert dry_run["tables"] == 1


def test_supply_core_supplier_certification_requires_human_authority():
    _, travel_supply_core, _ = _supply_modules()
    store = travel_supply_core.PostgresTravelSupplyStore()

    _assert_raises(
        PermissionError,
        "human_authority_approval_required",
        store.certify_supplier,
        supplier_id="11111111-1111-4111-8111-111111111111",
        human_authority_approved=False,
    )


def test_supply_core_input_validation_fails_before_database_write():
    _, travel_supply_core, _ = _supply_modules()
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


def test_travel_agency_exposes_direct_marketplace_without_false_live_claims(monkeypatch):
    _, _, postgres_db = _supply_modules()
    monkeypatch.setattr(
        postgres_db,
        "postgres_status",
        lambda: {"configured": False, "initialized": False},
    )
    current = travel_agency.status()

    assert current["oap_supply_core_software_ready"] is True
    assert current["oap_supply_core_schema_ready"] is False
    assert current["listing_photo_schema_ready"] is False
    assert current["oap_owns_direct_supplier_inventory_system"] is True
    assert current["oap_owns_supplier_inventory"] is False
    assert current["oap_owns_external_supplier_inventory"] is False
    assert current["direct_live_supply_ready"] is False
    assert current["booking_transactions_live"] is False
    assert current["payment_transactions_live"] is False
    assert current["pass_issuance_live"] is False
    assert current["commission_settlement_live"] is False

    gate_states = {gate["id"]: gate["ready"] for gate in current["gates"]}
    assert gate_states["oap_supply_core_software"] is True
    assert gate_states["oap_supply_core_schema"] is False
    assert gate_states["listing_photo_store"] is False
