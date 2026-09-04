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

    snapshot = travel_supply_views._operator_snapshot()

    assert snapshot["operator"]["supplier_ready"] is True
    assert snapshot["operator"]["owner_identity_id"] == "owner-founder"
    assert snapshot["operator"]["supplier_id"] == "supplier-certified"
    assert snapshot["operator"]["listing_id"] == "listing-live"
    assert snapshot["external_lookup"]["mode"] == "on_demand_only"
    assert snapshot["external_lookup"]["stored_partner_offers"] == 0
    assert snapshot["external_lookup"]["booking_com_partner"] is False


def test_booking_control_removes_uuid_copying_and_partner_import_from_primary_lane():
    page = _template()

    assert "supply.operator.owner_identity_id" in page
    assert "supply.operator.supplier_id" in page
    assert "Create real listing" in page
    assert "Add your pictures" in page
    assert "Human Authority · Activate" in page
    assert "Publish availability" in page
    assert "/mission/supply/partner/import" not in page
    assert 'action="/mission/supply/listings/media"' in page


def test_booking_control_public_links_escape_private_gateway():
    page = _template()

    public_origin = "https://on-any-postcode.onrender.com"
    assert f'href="{public_origin}/travel/direct"' in page
    assert 'href="/travel/direct"' not in page


def test_booking_control_keeps_external_lookup_truth_boundary():
    page = _template()

    assert "External lookup boundary" in page
    assert "not OAP partners" in page
    assert "does not import those offers" in page
    assert "does not use Booking.com for OAP reservation execution" in page
    assert (
        "Payment capture, OAP Pass issuance and commission settlement remain "
        "separately governed"
        in page
    )
