"""A public bank catalogue entry cannot become banking or installation."""
from mission_control import bank_store_listing


def test_public_bank_listing_is_always_non_installable() -> None:
    state = bank_store_listing.listing()
    assert state["name"] == "United States of Africa Royalty Bank"
    assert state["heritage"] == "Prince Sovereign Bank"
    assert state["app_id"] == "oap.usa_royalty_bank"
    assert state["informational_only"]
    assert state["public_release_state"] == "release_pending"
    for name in (
        "install_enabled", "package_available", "package_published",
        "banking_execution_enabled", "cash_services_enabled",
        "currency_issuance_enabled", "signed_package_verified",
        "separate_bank_pwa_verified",
    ):
        assert state[name] is False


def test_public_bank_routes_have_no_install_or_payment_methods(client) -> None:
    path = "/oap-store/apps/oap.usa_royalty_bank"
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json["install_enabled"] is False
    assert client.post(path).status_code == 405
    detail = client.get(path + "/view")
    assert detail.status_code == 200
    page = detail.get_data(as_text=True)
    assert "Installation unavailable" in page
    assert "No licence or operational banking status is claimed." in page
    assert "<button" not in page
    assert client.post(path + "/view").status_code == 405
