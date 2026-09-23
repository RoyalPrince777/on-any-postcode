"""Actual decorated HTTP tests for private Everyday form and record routes."""
import sqlite3

from flask import Flask

from mission_control import raffles_command_views as views
from oap.audit import initialize_audit_schema
from oap.everyday_records import initialize_schema


def client(tmp_path, monkeypatch):
    database = tmp_path / "actual-http.sqlite3"
    with sqlite3.connect(database) as connection:
        initialize_audit_schema(connection)
        connection.commit()
        initialize_schema(connection)
        connection.commit()
    monkeypatch.setattr(views.config, "OAP_DATABASE_PATH", str(database))
    monkeypatch.setattr(views.web_security, "csrf_valid", lambda _request: True)
    monkeypatch.setattr(views.web_security, "current_authenticated_user",
                        lambda: {"id": "offline-founder"})
    monkeypatch.setattr(views.web_security, "private_authority_allowed",
                        lambda _user: True)
    application = Flask(__name__)
    application.secret_key = "offline-only"
    application.register_blueprint(views.bp)
    return application.test_client(), database


def test_actual_http_partner_submit_and_readback(tmp_path, monkeypatch):
    browser, path = client(tmp_path, monkeypatch)
    response = browser.post(
        "/mission/raffles/everyday/propose",
        json={"kind": "partner", "organisation": "Neighbourhood shop",
              "prize": "Essentials voucher"},
    )
    assert response.status_code == 201
    receipt = response.get_json()
    assert receipt["ok"] is True
    assert receipt["status"] == "proposed_unverified"
    assert receipt["execution_granted"] is False
    listing = browser.get("/mission/raffles/everyday/records")
    assert listing.status_code == 200
    assert listing.get_json()["partners"][0]["organisation"] == "Neighbourhood shop"
    assert listing.get_json()["entries_open"] is False
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT count(*) FROM audit_events"
        ).fetchone()[0] == 1


def test_actual_http_invalid_resource_cannot_create_audit(tmp_path, monkeypatch):
    browser, path = client(tmp_path, monkeypatch)
    response = browser.post(
        "/mission/raffles/everyday/propose",
        json={"kind": "resource", "title": "Internal",
              "url": "http://example.org", "source": "Unknown",
              "checked_on": "2026-01-01"},
    )
    assert response.status_code == 400
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT count(*) FROM audit_events"
        ).fetchone()[0] == 0


def test_actual_http_without_founder_cannot_read_or_write(tmp_path, monkeypatch):
    browser, path = client(tmp_path, monkeypatch)
    monkeypatch.setattr(views.web_security, "private_authority_allowed",
                        lambda _user: False)
    assert browser.get("/mission/raffles/everyday/records").status_code == 403
    assert browser.post("/mission/raffles/everyday/propose",
                        json={"kind": "partner", "organisation": "Shop",
                              "prize": "Voucher"}).status_code == 403
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT count(*) FROM audit_events"
        ).fetchone()[0] == 0
