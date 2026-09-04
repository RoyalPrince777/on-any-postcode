from pathlib import Path

from mission_control import listing_media, travel_supply_policy
from oap.smi import supply_integration, supply_source_policy

ROOT = Path(__file__).resolve().parents[1]


def test_listing_media_migration_is_additive_and_first_party():
    assert listing_media.LISTING_MEDIA_MIGRATION_VERSION == "0009_oap_supply_listing_media"
    assert len(listing_media.LISTING_MEDIA_MIGRATION_CHECKSUM) == 64
    assert listing_media.LISTING_MEDIA_TABLE == "oap_supply_listing_media"
    assert listing_media.MAX_IMAGES_PER_LISTING == 8
    assert listing_media.MAX_IMAGE_BYTES == 5 * 1024 * 1024
    assert listing_media.ALLOWED_IMAGE_MIME_TYPES == {
        "image/jpeg",
        "image/png",
        "image/webp",
    }
    sql = "\n".join(listing_media.LISTING_MEDIA_SCHEMA_STATEMENTS).lower()
    assert "references oap_supply_listings" in sql
    assert "on delete cascade" in sql
    assert "bytea" in sql
    assert "booking.com" not in sql
    assert "http" not in sql


def test_booking_com_is_lookup_only_not_partner_or_booking_handoff():
    provider = supply_integration.provider("booking_com")
    assert provider is not None
    assert provider.provider_type == "optional_on_demand_external_lookup"
    assert provider.supports_search is True
    assert provider.supports_booking_handoff is False
    assert provider.supports_direct_booking is False
    assert provider.supports_payment is False
    status = supply_integration.runtime_provider_status("booking_com")
    assert status["partner_relationship"] is False
    assert status["persistent_import_allowed"] is False
    assert status["booking_handoff_supported"] is False


def test_travel_policy_has_no_partner_supply_lane():
    policy = travel_supply_policy.public_policy()
    assert policy["booking_com_partner"] is False
    assert policy["external_lookup_persisted"] is False
    assert policy["preferred_source_order"] == ["oap_direct"]
    source = supply_source_policy.status()
    assert source["external_suppliers_allowed"] is False
    assert source["external_lookup_allowed"] is True
    assert source["external_lookup_persisted"] is False
    assert source["booking_com_partner"] is False
    assert source["preferred_source_order"] == ("oap_direct",)


def test_founder_booking_ui_removed_partner_import_and_added_picture_upload():
    page = (ROOT / "mission_control/templates/travel_supply_control.html").read_text(
        encoding="utf-8"
    )
    assert "/mission/supply/partner/import" not in page
    assert "PARTNER SUPPLY" not in page
    assert 'action="/mission/supply/listings/media"' in page
    assert 'accept="image/jpeg,image/png,image/webp"' in page
    assert "External lookup boundary" in page


def test_public_travel_is_direct_only_and_can_render_oap_media():
    travel = (ROOT / "mission_control/templates/travel.html").read_text(encoding="utf-8")
    direct = (ROOT / "mission_control/templates/travel_direct.html").read_text(
        encoding="utf-8"
    )
    for page in (travel, direct):
        assert "cover_image_url" in page
        assert "Certified OAP Supplier" in page
    assert "catalogue.partner" not in travel
    assert "partner-card" not in travel
    assert "partner-title" not in travel
    assert "Fetch when needed. Do not import." in travel
