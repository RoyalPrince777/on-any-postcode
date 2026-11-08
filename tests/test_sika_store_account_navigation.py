"""SIKA Store discovery and account navigation remain non-financial and fail-closed."""
from mission_control import oap_store


def test_sika_store_entry_uses_existing_bank_identity_without_installation():
    entries = [item for item in oap_store.catalogue() if item["app_id"] == "oap.usa_royalty_bank"]
    assert len(entries) == 1
    item = entries[0]
    assert item["name"] == "United States of Africa Royalty Bank"
    assert item["release_state"] == "release_pending"
    assert item["open_url"] == "/oap-store/apps/oap.usa_royalty_bank/view"
    assert item["install_enabled"] is False
    assert item["install_url"] is None
    assert item["manifest_url"] is None
    assert item["native_package_available"] is False
    assert item["physical_device_certified"] is False


def test_sika_store_listing_is_discovery_only(client):
    response = client.get("/oap-store/apps")
    assert response.status_code == 200
    item = next(item for item in response.json["apps"] if item["app_id"] == "oap.usa_royalty_bank")
    assert item["install_enabled"] is False
    assert item["open_url"].endswith("/view")
    assert client.get(item["open_url"]).status_code == 200


def test_bank_home_offers_authenticated_account_door(client):
    response = client.get("/pay/bank")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'href="/pay/bank/me"' in page
    assert 'href="/store"' in page
    assert "My SIKA Account" in page
