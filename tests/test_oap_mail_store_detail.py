"""OAP Store details inform without implying a released installer or Mail."""
from __future__ import annotations

import pytest


@pytest.mark.parametrize("client_fixture", ["client", "anonymous_client"])
def test_store_detail_has_truthful_pending_state(request, client_fixture):
    client = request.getfixturevalue(client_fixture)
    response = client.get("/oap-store/apps/oap.mail/view")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "OAP Mail" in page
    assert "ON ANY POSTCODE LTD" in page
    assert "Release pending" in page
    assert "Open private Mail preview" in page
    assert 'href="/mail/app"' in page
    assert "Installation unavailable" in page
    assert "Email sending and receiving are not" in page
    assert "<form" not in page.lower()
    assert "download=" not in page.lower()
    assert "install_enabled" not in page.lower()


def test_public_store_preview_link_does_not_bypass_auth(anonymous_client):
    listing = anonymous_client.get("/oap-store/apps/oap.mail/view")
    assert listing.status_code == 200
    private = anonymous_client.get("/mail/app")
    assert private.status_code in (302, 303)
    assert private.headers["Cache-Control"] == "no-store"


def test_store_listing_stays_outside_private_mail_preview(client):
    private = client.get("/mail/app")
    assert private.status_code == 200
    page = private.get_data(as_text=True)
    assert 'href="/oap-store/apps/oap.mail/view"' not in page
    assert "OAP Store listing" not in page
    assert "Inbox" in page and "Drafts" in page


def test_store_detail_cannot_be_published_or_installed_via_post(client):
    for path in (
        "/oap-store/apps/oap.mail/view",
        "/oap-store/apps/oap.mail/install",
    ):
        response = client.post(path, json={"publish": True, "install": True})
        assert response.status_code in (404, 405)
