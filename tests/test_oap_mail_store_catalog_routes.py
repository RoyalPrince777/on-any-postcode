"""Read-only Store catalogue never implies Mail availability or installs."""
from __future__ import annotations

import pytest


@pytest.mark.parametrize("client_fixture", ["client", "anonymous_client"])
def test_mail_store_catalogue_is_read_only_and_release_pending(
    request, client_fixture,
):
    client = request.getfixturevalue(client_fixture)
    response = client.get("/oap-store/apps/oap.mail")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    data = response.get_json()
    assert data["app_id"] == "oap.mail"
    assert data["publisher"] == "ON ANY POSTCODE LTD"
    assert data["public_release_state"] == "release_pending"
    assert data["install_enabled"] is False
    assert data["package_available"] is False
    assert data["publish_executed"] is False
    assert data["mail_delivery_claimed"] is False
    assert "download_url" not in data
    assert "installer_url" not in data


def test_mail_store_catalogue_does_not_offer_write_or_install(client):
    for path in ("/oap-store/apps/oap.mail", "/oap-store/apps/oap.mail/install"):
        response = client.post(path, json={"install": True})
        assert response.status_code in (404, 405)
