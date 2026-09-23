"""Isolated ebook HTTP tests; no registration in the live OAP application."""

import pytest
from flask import Flask

from mission_control import oap_ebook_http, oap_ebook_service
from mission_control.oap_book_access import Book
from mission_control.oap_book_publication import EditionEvidence
from mission_control.oap_ebook_http import TrustedEbook, create_ebook_blueprint
from mission_control.oap_ebook_reader import EbookEdition, manuscript_digest

PAGES = ("first", "second")
DIGEST = manuscript_digest(PAGES)
MANUSCRIPT = EbookEdition("food-core", "v1", DIGEST, PAGES, frozenset({0}))
APPROVAL = EditionEvidence(
    "food-core", "v1", DIGEST, "creator", "publisher", "rights", "founder",
    rights_verified=True, manuscript_approved=True, public_release_approved=True,
)


@pytest.fixture
def reader(monkeypatch):
    monkeypatch.setattr(oap_ebook_http.web_security,
                        "current_authenticated_user", lambda: None)
    app = Flask(__name__)
    requested = []

    def resolve(book_id, edition_id):
        requested.append((book_id, edition_id))
        if (book_id, edition_id) != ("food-core", "v1"):
            return None
        return TrustedEbook(Book("food-core", core_free=True),
                            APPROVAL, MANUSCRIPT)

    app.register_blueprint(create_ebook_blueprint(resolve))
    return app.test_client(), requested


def test_free_ebook_page_has_secure_headers(reader):
    client, requested = reader
    result = client.get("/library/ebooks/food-core/v1/pages/0")
    assert result.status_code == 200
    assert result.json["content"] == "first"
    assert requested == [("food-core", "v1")]
    assert result.headers["Cache-Control"].startswith("private, no-store")
    assert "display-capture=()" in result.headers["Permissions-Policy"]


def test_unknown_or_invalid_selector_fails_closed(reader):
    client, requested = reader
    unknown = client.get("/library/ebooks/missing/v1/pages/0")
    assert unknown.status_code == 404
    invalid = client.get("/library/ebooks/food.core/v1/pages/0")
    assert invalid.status_code == 400
    assert requested == [("missing", "v1")]
    assert "no-store" in unknown.headers["Cache-Control"]


def test_page_bound_and_no_purchase_claim_from_request(reader):
    client, _ = reader
    assert client.get("/library/ebooks/food-core/v1/pages/9").status_code == 404
    assert client.get(
        "/library/ebooks/food-core/v1/pages/0",
        query_string={"purchased": "true", "rights_verified": "true"},
    ).status_code == 200


def test_unverified_edition_returns_no_content(monkeypatch):
    monkeypatch.setattr(oap_ebook_http.web_security,
                        "current_authenticated_user", lambda: None)
    app = Flask(__name__)
    unapproved = EditionEvidence(
        "food-core", "v1", DIGEST, "creator", "publisher", "rights",
        "founder", manuscript_approved=True,
    )
    app.register_blueprint(create_ebook_blueprint(
        lambda _book, _edition: TrustedEbook(
            Book("food-core", core_free=True), unapproved, MANUSCRIPT,
        )
    ))
    response = app.test_client().get("/library/ebooks/food-core/v1/pages/0")
    assert response.status_code == 404
    assert "content" not in response.json


def test_paid_book_cannot_be_unlocked_by_url_flags(monkeypatch):
    monkeypatch.setattr(oap_ebook_http.web_security,
                        "current_authenticated_user", lambda: None)
    app = Flask(__name__)
    app.register_blueprint(create_ebook_blueprint(
        lambda _book, _edition: TrustedEbook(
            Book("food-core", premium=True), APPROVAL, MANUSCRIPT,
        )
    ))
    response = app.test_client().get(
        "/library/ebooks/food-core/v1/pages/0",
        query_string={"paid": "1", "owner_id": "anyone"},
    )
    assert response.status_code == 404
    assert "content" not in response.json


def test_entitlement_store_failure_is_unavailable(monkeypatch):
    monkeypatch.setattr(oap_ebook_http.web_security,
                        "current_authenticated_user", lambda: {"id": "member"})
    def broken(**_kwargs):
        raise oap_ebook_http.BookEntitlementsUnavailable("offline")

    monkeypatch.setattr(oap_ebook_service, "lookup_verified_purchase", broken)
    app = Flask(__name__)
    app.register_blueprint(create_ebook_blueprint(
        lambda _book, _edition: TrustedEbook(
            Book("food-core", premium=True), APPROVAL, MANUSCRIPT,
        )
    ))
    result = app.test_client().get("/library/ebooks/food-core/v1/pages/0")
    assert result.status_code == 503
    assert "content" not in result.json
    assert "no-store" in result.headers["Cache-Control"]
