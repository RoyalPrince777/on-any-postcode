"""Public OAP Mail Store information may ship without mailbox release."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.parametrize("fixture", ["client", "anonymous_client"])
def test_mail_store_information_is_public_and_not_an_installer(request, fixture):
    visitor = request.getfixturevalue(fixture)
    response = visitor.get("/oap-store/apps/oap.mail")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    listing = response.get_json()
    assert listing["app_id"] == "oap.mail"
    assert listing["publisher"] == "ON ANY POSTCODE LTD"
    assert listing["first_party"] is True
    assert listing["informational_only"] is True
    assert listing["public_release_state"] == "release_pending"
    for key in (
        "mailbox_available", "delivery_enabled", "install_enabled",
        "package_available", "publish_executed", "mail_delivery_claimed",
        "end_to_end_encryption_claimed", "security_certification_claimed",
    ):
        assert listing[key] is False
    assert "download_url" not in listing
    assert "installer_url" not in listing


@pytest.mark.parametrize("fixture", ["client", "anonymous_client"])
def test_mail_store_html_is_information_only(request, fixture):
    visitor = request.getfixturevalue(fixture)
    response = visitor.get("/oap-store/apps/oap.mail/view")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "OAP Mail" in html
    assert "ON ANY POSTCODE LTD" in html
    assert "Release pending" in html
    assert "Installation unavailable" in html
    assert "Email sending and receiving are not released" in html
    assert "not the private Mail application" in html
    assert "<form" not in html.casefold()
    assert 'href="/mail/app"' not in html
    assert "download=" not in html
    assert "/mail/drafts" not in html


def test_information_does_not_expose_store_write_or_installer_paths(client):
    for path in (
        "/oap-store/apps/oap.mail",
        "/oap-store/apps/oap.mail/view",
        "/oap-store/apps/oap.mail/install",
    ):
        assert client.post(path, json={"install": True}).status_code in (404, 405)
    # Store information stays inert even if a separate authenticated,
    # unreleased private Mail preview is registered in the same app.
    page = client.get("/oap-store/apps/oap.mail/view").get_data(as_text=True)
    assert "not the private Mail application" in page
    assert 'href="/mail/app"' not in page
    assert "/mail/drafts" not in page


def test_catalogue_module_has_no_transport_database_or_package_dependencies():
    source = Path("mission_control/mail_store_catalog_routes.py").read_text()
    listing = Path("mission_control/mail_store_listing.py").read_text()
    for prohibited in (
        "postgres_db", "mail_routes", "mail_store.", "mail_migration",
        "smtp", "send_message", "install_package", "mail_transport",
    ):
        assert prohibited not in source
        assert prohibited not in listing
