"""Actual Raffles STOP HTTP-to-SQLite contract; no public actions."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import Flask

from mission_control import raffles_command_views as views
from oap.audit import initialize_audit_schema
from oap.raffles_durable import initialize_schema, status

ROOT = Path(__file__).resolve().parents[1]


def app():
    test_app = Flask(__name__)
    test_app.secret_key = "offline-test"
    return test_app


def prepared(tmp_path, monkeypatch):
    database = tmp_path / "canonical.sqlite3"
    with sqlite3.connect(database) as conn:
        initialize_audit_schema(conn)
        conn.commit()
        initialize_schema(conn)
        conn.commit()
    monkeypatch.setattr(views.config, "OAP_DATABASE_PATH", str(database))
    monkeypatch.setattr(views.web_security, "csrf_valid", lambda _request: True)
    monkeypatch.setattr(views.web_security, "current_authenticated_user",
                        lambda: {"id": "founder-id"})
    return database


def post(action):
    with app().test_request_context("/mission/raffles/stop-control",
                                    method="POST", json={"action": action,
                                                         "campaign_id": "everyday-rewards"}):
        return views.stop_control.__wrapped__()


def test_stop_actual_receipt_restart_and_unreleased(tmp_path, monkeypatch):
    path = prepared(tmp_path, monkeypatch)
    response = post("STOP")
    data = response.get_json()
    assert response.status_code == 200 and data["ok"] is True
    assert data["outcome"] == "STOPPED" and data["receipt_seq"] == 1
    assert data["execution_granted"] is False
    with sqlite3.connect(path) as conn:
        assert status(conn, "everyday-rewards")["stopped"]
        assert conn.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 1


def test_recovery_requires_real_canonical_authority(tmp_path, monkeypatch):
    path = prepared(tmp_path, monkeypatch)

    @contextmanager
    def canonical(**_kwargs):
        yield object()

    monkeypatch.setattr(views.postgres_db, "connect", canonical)
    def deny(_connection, _actor):
        raise PermissionError("level_zero_required")
    monkeypatch.setattr(views.authority, "require_human_authority", deny)
    assert post("RECOVER").status_code == 403
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 0
    monkeypatch.setattr(views.authority, "require_human_authority",
                        lambda _connection, _actor: {"is_human_authority": True})
    result = post("RECOVER").get_json()
    assert result["outcome"] == "RECOVERED_TO_REVIEW"
    assert not result["execution_granted"] and not result["release_allowed"]


def test_missing_schema_denies_with_no_false_receipt(tmp_path, monkeypatch):
    path = prepared(tmp_path, monkeypatch)
    with sqlite3.connect(path) as conn:
        conn.execute("DROP TABLE audit_events")
        conn.commit()
    response = post("STOP")
    assert response.status_code == 503 and not response.get_json()["ok"]
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM raffles_stop_state").fetchone()[0] == 0


def test_csrf_is_checked_before_audit(tmp_path, monkeypatch):
    path = prepared(tmp_path, monkeypatch)
    monkeypatch.setattr(views.web_security, "csrf_valid", lambda _request: False)
    assert post("STOP").status_code == 403
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 0


def test_buttons_address_real_stop_endpoint():
    source = (ROOT / "mission_control/templates/raffles_command.html").read_text()
    assert '"/mission/raffles/stop-control"' in source
    assert 'campaign_id:"everyday-rewards"' in source
    assert 'data-action="STOP"' in source
    assert 'data-action="RECOVER"' in source
