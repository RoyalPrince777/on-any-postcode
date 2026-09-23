"""Everyday authenticated private form-to-audit-to-readback contracts."""
import sqlite3
from pathlib import Path

from flask import Flask

from mission_control import raffles_command_views as views
from oap.audit import initialize_audit_schema
from oap.everyday_records import initialize_schema

ROOT = Path(__file__).resolve().parents[1]


def app():
    test_app = Flask(__name__)
    test_app.secret_key = "offline-only"
    return test_app


def prepared(tmp_path, monkeypatch, *, schema=True):
    database = tmp_path / "oap.sqlite3"
    with sqlite3.connect(database) as connection:
        initialize_audit_schema(connection)
        connection.commit()
        if schema:
            initialize_schema(connection)
            connection.commit()
    monkeypatch.setattr(views.config, "OAP_DATABASE_PATH", str(database))
    monkeypatch.setattr(views.web_security, "csrf_valid", lambda _request: True)
    monkeypatch.setattr(views.web_security, "current_authenticated_user",
                        lambda: {"id": "signed-in-founder-uuid"})
    return database


def propose(payload):
    with app().test_request_context("/mission/raffles/everyday/propose",
                                    method="POST", json=payload):
        return views.everyday_propose.__wrapped__()


def listing():
    with app().test_request_context("/mission/raffles/everyday/records"):
        return views.everyday_records.__wrapped__()


def test_partner_button_to_persistence_to_audit(tmp_path, monkeypatch):
    path = prepared(tmp_path, monkeypatch)
    result = propose({"kind": "partner", "organisation": "Local shop",
                      "prize": "Essentials voucher"})
    assert result.status_code == 201
    assert result.get_json()["status"] == "proposed_unverified"
    assert result.get_json()["public_listing_allowed"] is False
    read = listing().get_json()
    assert len(read["partners"]) == 1
    assert read["partners"][0]["organisation"] == "Local shop"
    assert read["entries_open"] is False and read["payments_enabled"] is False
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 1


def test_private_resource_submitted_not_published(tmp_path, monkeypatch):
    path = prepared(tmp_path, monkeypatch)
    response = propose({"kind": "resource", "title": "Support source",
                        "url": "https://example.org/support",
                        "source": "Example", "checked_on": "2026-01-01"})
    assert response.status_code == 201
    assert response.get_json()["published"] is False
    assert listing().get_json()["resources"][0]["status"] == "private_review"
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 1


def test_missing_schema_and_invalid_link_are_blocked(tmp_path, monkeypatch):
    prepared(tmp_path, monkeypatch, schema=False)
    denied = propose({"kind": "partner", "organisation": "Shop",
                      "prize": "Voucher"})
    assert denied.status_code == 503 and denied.get_json()["ok"] is False
    assert listing().status_code == 503
    path = prepared(tmp_path, monkeypatch, schema=True)
    invalid = propose({"kind": "resource", "title": "Wrong",
                       "url": "http://example.org", "source": "None",
                       "checked_on": "2026-01-01"})
    assert invalid.status_code == 400
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 0


def test_csrf_and_anonymous_cannot_write(tmp_path, monkeypatch):
    path = prepared(tmp_path, monkeypatch)
    monkeypatch.setattr(views.web_security, "csrf_valid", lambda _request: False)
    assert propose({"kind": "partner", "organisation": "Shop",
                    "prize": "Voucher"}).status_code == 403
    monkeypatch.setattr(views.web_security, "csrf_valid", lambda _request: True)
    monkeypatch.setattr(views.web_security, "current_authenticated_user",
                        lambda: None)
    assert propose({"kind": "partner", "organisation": "Shop",
                    "prize": "Voucher"}).status_code == 401
    assert listing().status_code == 401
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 0


def test_real_button_and_form_wiring_in_founder_page():
    source = (ROOT / "mission_control/templates/everyday_command.html").read_text()
    assert 'form data-kind="partner"' in source
    assert 'form data-kind="resource"' in source
    assert '"/mission/raffles/everyday/propose"' in source
    assert '"/mission/raffles/everyday/records"' in source
    assert 'credentials:"same-origin"' in source
    assert "button.disabled=true" in source
    assert "role=\"status\"" in source
