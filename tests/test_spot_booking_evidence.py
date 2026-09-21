from pathlib import Path


def test_spot_booking_evidence_boot_snapshot_is_read_only_and_redacted():
    source = Path("mission_control/__init__.py").read_text(encoding="utf-8")
    block = source.split(
        'OAP_SPOT_BOOKING_EVIDENCE_ON_BOOT', 1
    )[1].split(
        'OAP_AEGIS_75_PROOF_ON_BOOT', 1
    )[0]

    assert "travel_supply_core.status()" in block
    assert "listing_media.status()" in block
    assert "travel_marketplace.public_offers(limit=100)" in block
    assert '"event": "oap_spot_booking_evidence"' in block
    for field in (
        "certified_supplier_count",
        "active_listing_count",
        "live_inventory_slot_count",
        "confirmed_reservation_count",
        "direct_booking_runtime_ready",
        "listing_media_schema_ready",
        "listing_photo_count",
        "public_offer_count",
    ):
        assert field in block
    assert '"payment_capture_live": False' in block
    assert '"dispatch_enabled": False' in block
    assert '"execution_granted": False' in block
    assert '"secret_exposed": False' in block
    assert '"read_only": True' in block

    forbidden = (
        "owner_identity_id",
        "supplier_id",
        "listing_id",
        "reservation_id",
        "buyer_identity_id",
        "payment_intent",
        "DATABASE_URL",
    )
    for marker in forbidden:
        assert marker not in block
