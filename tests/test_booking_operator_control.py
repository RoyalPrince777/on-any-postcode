from pathlib import Path

from mission_control import travel_supply_views


ROOT = Path(__file__).resolve().parents[1]


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
        travel_supply_views.partner_supply,
        "status",
        lambda: {"schema": {"schema_ready": True}},
    )

    snapshot = travel_supply_views._operator_snapshot()

    assert snapshot["operator"]["supplier_ready"] is True
    assert snapshot["operator"]["owner_identity_id"] == "owner-founder"
    assert snapshot["operator"]["supplier_id"] == "supplier-certified"
    assert snapshot["operator"]["listing_id"] == "listing-live"
    assert snapshot["partner_supply"]["schema"]["schema_ready"] is True


def test_booking_control_removes_uuid_copying_from_primary_lane():
    page = (ROOT / "mission_control/templates/travel_supply_control.html").read_text(
        encoding="utf-8"
    )

    assert "No UUID copying is needed" in page
    assert "supply.operator.owner_identity_id" in page
    assert "supply.operator.supplier_id" in page
    assert "Create real listing" in page
    assert "Human Authority · Activate" in page
    assert "Publish availability" in page
    assert "data-json-endpoint=\"/mission/supply/partner/import\"" in page


def test_booking_control_public_links_escape_private_gateway():
    page = (ROOT / "mission_control/templates/travel_supply_control.html").read_text(
        encoding="utf-8"
    )

    public_origin = "https://on-any-postcode.onrender.com"
    assert f'href="{public_origin}/travel/direct"' in page
    assert f'href="{public_origin}/travel/api/catalogue"' in page
    assert f'href="{public_origin}/travel/partner/api/offers"' in page
    assert 'href="/travel/direct"' not in page


def test_booking_control_keeps_external_provider_truth_boundary():
    page = (ROOT / "mission_control/templates/travel_supply_control.html").read_text(
        encoding="utf-8"
    )

    assert "Maximum life is 24 hours" in page
    assert "not booking authority" in page
    assert "Payment capture, OAP Pass issuance and commission settlement remain separately governed" in page
