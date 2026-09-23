"""Full Flask route → first-party SQLite → canonical audit integration."""
import sqlite3

from flask import Flask

from mission_control import raffles_command_views as views
from oap.audit import initialize_audit_schema
from oap.everyday_records import initialize_schema


def setup(tmp_path, monkeypatch):
    database = tmp_path / "oap.sqlite3"
    with sqlite3.connect(database) as connection:
        initialize_audit_schema(connection)
        connection.commit()
        initialize_schema(connection)
        connection.commit()
    monkeypatch.setattr(views.config, "OAP_DATABASE_PATH", str(database))
    monkeypatch.setattr(views.web_security, "csrf_valid", lambda _request: True)
    monkeypatch.setattr(views.web_security, "current_authenticated_user",
                        lambda: {"id": "private-founder"})
    monkeypatch.setattr(views.web_security, "private_authority_allowed",
                        lambda _user: True)
    app = Flask(__name__)
    app.secret_key = "offline-test-only"
    app.register_blueprint(views.bp)
    return app.test_client(), database


def test_actual_authenticated_routes_save_and_read(tmp_path, monkeypatch):
    client, path = setup(tmp_path, monkeypatch)
    response = client.post("/mission/raffles/everyday/propose",
                           json={"kind": "partner", "organisation": "Local shop",
                                 "prize": "Essentials voucher"})
    assert response.status_code == 201
    body = response.get_json()
    assert body["ok"] is True and body["prize_secured"] is False
    read = client.get("/mission/raffles/everyday/records")
    assert read.status_code == 200
    assert len(read.get_json()["partners"]) == 1
    assert read.get_json()["public_listing_allowed"] is False
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 1


def test_actual_auth_and_csrf_fail_closed(tmp_path, monkeypatch):
    client, path = setup(tmp_path, monkeypatch)
    monkeypatch.setattr(views.web_security, "current_authenticated_user",
                        lambda: None)
    assert client.get("/mission/raffles/everyday/records").status_code == 401
    assert client.post("/mission/raffles/everyday/propose",
                       json={"kind": "partner", "organisation": "Shop",
                             "prize": "Voucher"}).status_code == 401
    monkeypatch.setattr(views.web_security, "current_authenticated_user",
                        lambda: {"id": "not-founder"})
    monkeypatch.setattr(views.web_security, "private_authority_allowed",
                        lambda _user: False)
    assert client.get("/mission/raffles/everyday/records").status_code == 403
    monkeypatch.setattr(views.web_security, "private_authority_allowed",
                        lambda _user: True)
    monkeypatch.setattr(views.web_security, "csrf_valid", lambda _request: False)
    assert client.post("/mission/raffles/everyday/propose",
                       json={"kind": "partner", "organisation": "Shop",
                             "prize": "Voucher"}).status_code == 403
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 0
