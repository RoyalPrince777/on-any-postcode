from mission_control import travel_supply_views


def _template() -> str:
    with open(
        "mission_control/templates/travel_supply_control.html",
        encoding="utf-8",
    ) as handle:
        return handle.read()


def test_operator_snapshot_prefers_certified_supplier_and_active_listing(monkeypatch):
    monkeypatch.setattr(
        travel_supply_views.travel_marketplace,
        "founder_snapshot",
        lambda: {
            "suppliers": [
                {
                    "supplier_id": "supplier-certified",
                    "owner_identity_id": "owner-founder",
                    "display_name": "ON ANY POSTCODE LTD",
                    "state": "CERTIFIED",
                    "commercial_terms_state": "CERTIFIED",
                }
            ],
            "listings": [
                {
                    "listing_id": "listing-live",
                    "title": "Real listing",
                    "state": "ACTIVE",
                }
            ],
        },
    )
    monkeypatch.setattr(
        travel_supply_views.listing_media,
        "photo_map",
        lambda _ids: {"listing-live": []},
    )
    monkeypatch.setattr(
        travel_supply_views.listing_media,
        "status",
        lambda: {"schema_ready": True, "photo_count": 0},
    )

    snapshot = travel_supply_views._operator_snapshot()

    assert snapshot["operator"]["supplier_ready"] is True
    assert snapshot["operator"]["owner_identity_id"] == "owner-founder"
    assert snapshot["operator"]["supplier_id"] == "supplier-certified"
    assert snapshot["operator"]["listing_id"] == "listing-live"
    assert snapshot["listing_media"]["schema_ready"] is True
    assert snapshot["listings"][0]["photo_count"] == 0
    assert snapshot["travel_policy"]["external_catalogue_import_allowed"] is False


def test_booking_control_primary_lane_is_direct_and_photo_ready():
    page = _template()

    assert "supply.operator.owner_identity_id" in page
    assert "supply.operator.supplier_id" in page
    assert "Create real listing" in page
    assert "Add authorised listing photos" in page
    assert "Human Authority · Activate" in page
    assert "Publish availability" in page
    assert 'data-endpoint="/mission/supply/listings/photos"' in page
    assert 'data-json-endpoint="/mission/supply/partner/import"' not in page


def test_booking_control_public_links_escape_private_gateway():
    page = _template()

    public_origin = "https://on-any-postcode.onrender.com"
    assert f'href="{public_origin}/travel/direct"' in page
    assert f'href="{public_origin}/travel/api/catalogue"' in page
    assert f'href="{public_origin}/travel/partner/api/offers"' not in page
    assert 'href="/travel/direct"' not in page


def test_booking_control_keeps_external_data_and_media_truth_boundary():
    page = _template()

    assert "External marketplace partnerships are disabled" in page
    assert "research only" in page
    assert "I own these pictures or have permission to use them" in page
    assert "Do not copy marketplace photos unless you have permission" in page
    assert (
        "Payment capture, OAP Pass issuance and commission settlement remain "
        "separately governed"
        in page
    )
