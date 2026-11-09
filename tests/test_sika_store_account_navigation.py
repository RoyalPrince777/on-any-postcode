"""SIKA Store discovery and account navigation remain non-financial and fail-closed."""
from mission_control import oap_store


def test_sika_store_entry_uses_existing_bank_identity_without_installation():
    entries = [item for item in oap_store.catalogue() if item["app_id"] == "oap.usa_royalty_bank"]
    assert len(entries) == 1
    item = entries[0]
    assert item["name"] == "United States of Africa Royalty Bank"
    assert item["release_state"] == "release_pending"
    assert item["open_url"] == "/oap-store/apps/oap.usa_royalty_bank/view"
    assert item["browser_url"] == "/pay/bank"
    assert item["browser_account_url"] == "/pay/bank/me"
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


def test_bank_browser_access_without_install(client):
    page = client.get("/store").get_data(as_text=True)
    assert 'href="/pay/bank">Open in Browser</a>' in page
    assert 'href="/pay/bank/me">My SIKA Account · Sign in</a>' in page
    assert "Browser access requires no installation" in page
    detail = client.get("/oap-store/apps/oap.usa_royalty_bank/view")
    assert detail.status_code == 200
    assert 'href="/pay/bank"' in detail.get_data(as_text=True)
    assert 'href="/pay/bank/me"' in detail.get_data(as_text=True)


def test_bank_public_page_never_claims_install_ready(client):
    page = client.get("/pay/bank").get_data(as_text=True)
    assert "Browser access" in page
    assert "Install unavailable" in page
    assert "Install OAP Bank" not in page
    assert "data-oap-install hidden" not in page


def test_sika_menu_has_five_clear_tabs_with_real_routes(client):
    page = client.get("/pay/bank").get_data(as_text=True)
    assert 'href="#home"><strong>⌂</strong>Home' in page
    assert 'href="/pay/bank/me"><strong>▤</strong>Wallet' in page
    assert 'href="/pay/bank/cards"><strong>▣</strong>Card' in page
    assert 'href="/pay/bank/activity"><strong>≡</strong>Activity' in page
    assert 'href="#more"><strong>•••</strong>More' in page
    assert "Full menu" in page
    assert 'href="/store"' in page
    assert 'href="/world"' in page
    assert "Install OAP Bank" not in page
